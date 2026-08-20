from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.graph.build_graph import graph
from app.graph.state import ResearchState

app = FastAPI(title="Multi-Agent Research & Report Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class ReportResponse(BaseModel):
    report: str
    topics: list[str]
    rating: int
    loop_count: int
    critic_feedback: str

@app.post("/research", response_model=ReportResponse)
async def research(payload: QuestionRequest):
    initial_state = ResearchState(question=payload.question)
    result = await graph.ainvoke(initial_state)

    return ReportResponse(
        report=result["report"],
        topics=result["topics"],
        rating=result["rating"],
        loop_count=result["loop_count"],
        critic_feedback=result["critic_feedback"],
    )

@app.get("/health")
def health():
    return {"status": "ok"}