from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.graph.build_graph import graph
from app.graph.state import ResearchState

app = FastAPI(title="Multi-Agent Research & Report Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


def sse_event(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


@app.post("/research/stream")
async def research_stream(payload: QuestionRequest):
    async def event_generator():
        initial_state = ResearchState(question=payload.question)
        accumulated = initial_state.model_dump()

        async for chunk in graph.astream(initial_state):
            for node_name, node_output in chunk.items():
                accumulated.update(node_output)
                yield sse_event("stage", {"node": node_name, "status": "done"})

        yield sse_event("result", {
            "report": accumulated["report"],
            "topics": accumulated["topics"],
            "rating": accumulated["rating"],
            "loop_count": accumulated["loop_count"],
            "critic_feedback": accumulated["critic_feedback"],
        })

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}
@app.get("/health")
def health():
    return {"status": "ok"}