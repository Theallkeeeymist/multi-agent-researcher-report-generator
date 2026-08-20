from typing import List
from pydantic import BaseModel, Field

class ResearchState(BaseModel):
    """
    Represents the state of a research project.
    """
    question: str = Field(..., description="The research question being investigated.")
    topics: List[str] = Field(default_factory=list, description="A list of topics related to the research question.")
    answer: str = Field(default="", description="The answer or findings related to the research question.")
    loop_count: int = Field(default=0, description="Number of researcher↔critic iterations so far.")
    rating: int = Field(default=0, ge=0, le=5, description="The rating of the critic node, indicating the quality of the research findings.")
    critic_feedback: str = Field(default="", description="Feedback provided by the critic node.")
    report: str = Field(default="", description="A detailed report summarizing the research findings and conclusions.")

class CriticOutput(BaseModel):
    rating: int = Field(default=0, ge=0, le=5, description="The rating of the critic node, indicating the quality of the research findings.")
    feedback: str = Field(default="", description="Feedback provided by the critic node.")