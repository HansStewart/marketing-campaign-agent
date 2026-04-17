"""LangGraph state definition for the marketing campaign agent."""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class CampaignState(TypedDict):
    """Full state passed through every node in the LangGraph campaign agent."""

    # Inputs
    campaign_brief: str
    target_audience: str
    offer: str
    platform: str
    tone: str

    # Strategist outputs
    research_insights: Optional[str]
    messaging_angles: Optional[List[str]]

    # Copywriter outputs
    copy_variants: Optional[List[str]]

    # Evaluator outputs
    evaluation_scores: Optional[List[float]]
    evaluation_feedback: Optional[str]
    approved: bool

    # Human review outputs
    human_approved: Optional[bool]
    human_feedback: Optional[str]

    # Best variant tracking
    best_variant: Optional[str]
    best_variant_score: Optional[float]

    # Email sequence output
    email_sequence: Optional[List[Dict[str, Any]]]

    # Control flow
    revision_count: int
    max_revisions: int
    metadata: Dict[str, Any]