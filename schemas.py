"""Pydantic structured output schemas for LangChain nodes in the campaign agent."""

from typing import List

from pydantic import BaseModel, Field


class StrategyOutput(BaseModel):
    """Output from the strategist node."""

    research_insights: str = Field(description="Key market research insights")
    messaging_angles: List[str] = Field(description="3 distinct messaging angles")


class CopyOutput(BaseModel):
    """Output from the copywriter node."""

    variants: List[str] = Field(description="3 campaign copy variants")


class EvaluationOutput(BaseModel):
    """Output from the evaluator node."""

    scores: List[float] = Field(description="Score (1-10) for each variant")
    feedback: str = Field(description="Feedback on weaknesses and improvement areas")
    approved: bool = Field(description="Whether the best variant meets the quality threshold")
    best_variant_index: int = Field(description="Index of the best scoring variant")


class EmailItem(BaseModel):
    """A single follow-up email."""

    subject: str = Field(description="Email subject line")
    body: str = Field(description="Full email body text")
    send_day: int = Field(description="Day after initial contact to send this email (e.g. 1, 3, 7)")


class EmailSequenceOutput(BaseModel):
    """Output from the email sequence node — 3 follow-up emails."""

    emails: List[EmailItem] = Field(description="List of 3 follow-up emails in sequence")
    strategy_note: str = Field(description="Brief note on the email strategy used")