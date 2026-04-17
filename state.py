from typing import Any, Dict, List, Optional, TypedDict


class CampaignState(TypedDict):
    campaign_brief: str
    target_audience: str
    offer: str
    platform: str
    tone: str

    research_insights: Optional[List[str]]
    messaging_angles: Optional[List[str]]
    copy_variants: Optional[List[str]]

    evaluation_scores: Optional[List[float]]
    evaluation_feedback: Optional[str]
    approved: bool

    human_approved: Optional[bool]
    human_feedback: Optional[str]
    human_reject_reason: Optional[str]
    human_reject_severity: Optional[str]
    human_tags: Optional[List[str]]

    best_variant: Optional[str]
    best_variant_score: Optional[float]
    email_sequence: Optional[List[Dict[str, Any]]]

    revision_count: int
    max_revisions: int
    metadata: Dict[str, Any]