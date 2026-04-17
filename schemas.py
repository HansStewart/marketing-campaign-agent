from pydantic import BaseModel, Field
from typing import List


class StrategyOutput(BaseModel):
    research_insights: str = Field(description="Strategic marketing analysis")
    messaging_angles: List[str] = Field(description="Exactly 3 messaging angles")


class CopyOutput(BaseModel):
    variants: List[str] = Field(description="Exactly 3 campaign copy variants")


class EvaluationOutput(BaseModel):
    scores: List[float] = Field(description="Exactly 3 scores, one per variant")
    best_variant_index: int = Field(description="Zero-based index of best variant")
    approved: bool = Field(description="Whether at least one variant meets approval threshold")
    feedback: str = Field(description="Revision guidance or approval rationale")