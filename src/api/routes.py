import os, asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery import Celery
from celery.result import AsyncResult

from tools.mcp_client import start_mcp_session, stop_mcp_session
from agent.build_graph import graph
from agent.state import ResearchState


app = FastAPI(title="Multi-Agent Research & Report Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery(
    "research_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Function is executed at the background "worker" container, NOT the API.
@celery_app.task(bind=True)
def run_research_task(self, question:str):
    """
    Celery is sync while graph and MCP previously created were Async
    so defining an inner async function and running it using asyncio.run()
    """
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


@app.post("/research", response_model=TaskResponse)
async def research(payload: QuestionRequest):
    # .delay() drops the prompt into Redis and immediately returns a ticket.
    task = run_research_task.delay(payload.question)

    return TaskResponse(task_id=task.id, status="Processing")

@app.get("/research/status/{task_id}")
async def get_status(task_id: str):
    # Streamlit will poll this endpoint to check if the worker is done.
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.ready():
        if task_result.successful():
            return {"status": "Completed", "result": task_result.result}
        else:
            return {"status": "Failed", "error": str(task_result.info)}
    else:
        {"status": task_result.state}


@app.get("/health")
def health():
    return {"status": "ok"}