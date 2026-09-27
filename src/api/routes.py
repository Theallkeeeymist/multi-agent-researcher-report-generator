import os, asyncio
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from celery import Celery
from celery.result import AsyncResult
from authlib.integrations.starlette_client import OAuth

from src.tools.mcp_client import start_mcp_session, stop_mcp_session
from src.agent.build_graph import graph
from src.agent.state import ResearchState

app = FastAPI(title="Multi-Agent Research & Report Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "super-secret-default")
)

REDIS_URL = os.getenv("REDIS_URL")
celery_app = Celery(
    "research_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

router = APIRouter()
oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope':'openid email profile'},
)

@router.get("/auth/login")
async def login(request: Request):
    """Triggered by streamlit Login button"""
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/callback")
async def auth_callback(request: Request):
    """Google redirects here. We get the token and send the user back to streamlit."""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')

    if not user_info:
        raise HTTPException(status_code=400, detail="Authentication failed")

    id_token = token.get('id_token')
    return RedirectResponse(url=f"http://localhost:8501/?token={id_token}")

# FIX 2: Register the router with the main app!
app.include_router(router)

def verify_token(request: Request):
    """Dependency to protect the /research route."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@celery_app.task(bind=True)
def run_research_task(self, question:str):
    async def execute_graph():
        await start_mcp_session()
        try:
            initial_state = ResearchState(question=question)
            result = await graph.ainvoke(initial_state)

            return {
                "report": result.get("report", ""),
                "topics": result.get("topics", []),
                "rating": result.get("rating", 0),
                "loop_count": result.get("loop_count", 0),
                "critic_feedback": result.get("critic_feedback", "")
            }
        finally:
            await stop_mcp_session()

    return asyncio.run(execute_graph())

class QuestionRequest(BaseModel):
    question: str

class TaskResponse(BaseModel):
    task_id: str
    status: str

# FIX 3: Protect the route using the dependency
@app.post("/research", response_model=TaskResponse, dependencies=[Depends(verify_token)])
async def research(payload: QuestionRequest):
    task = run_research_task.delay(payload.question)
    return TaskResponse(task_id=task.id, status="Processing")

@app.get("/research/status/{task_id}")
async def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.ready():
        if task_result.successful():
            return {"status": "Completed", "result": task_result.result}
        else:
            return {"status": "Failed", "error": str(task_result.info)}
    else:
        return {"status": task_result.state}

@app.get("/health")
def health():
    return {"status": "ok"}