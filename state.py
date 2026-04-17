from typing import TypedDict, List, Optional, Dict, Any


class CampaignState(TypedDict):
    campaign_brief: str
    target_audience: str
    offer: str
    platform: str
    tone: str

    research_insights: Optional[str]
    messaging_angles: Optional[List[str]]
    copy_variants: Optional[List[str]]

    evaluation_scores: Optional[List[float]]
    evaluation_feedback: Optional[str]
    approved: bool

    human_approved: Optional[bool]
    human_feedback: Optional[str]

    best_variant: Optional[str]
    best_variant_score: Optional[float]

    revision_count: int
    max_revisions: int

    metadata: Dict[str, Any]