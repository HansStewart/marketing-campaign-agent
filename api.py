from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from graph import build_graph


app = FastAPI(
    title="Marketing Campaign Agent API",
    version="1.0.0",
    description="HTTP API for the LangGraph-based marketing campaign agent.",
)

graph = build_graph()


class CampaignRequest(BaseModel):
    campaign_brief: str
    target_audience: str
    offer: str
    platform: str
    tone: Optional[str] = None
    max_revisions: int = 0


class EmailItem(BaseModel):
    subject: str
    body: str
    send_day: int


class CampaignResponse(BaseModel):
    best_variant: Optional[str]
    evaluation_scores: Optional[List[float]]
    best_variant_score: Optional[float]
    email_sequence: Optional[List[EmailItem]]
    raw_state: Dict[str, Any]


@app.post("/campaign", response_model=CampaignResponse)
def run_campaign(req: CampaignRequest) -> CampaignResponse:
    """Run the campaign agent once and return the core outputs."""
    state: Dict[str, Any] = {
        "campaign_brief": req.campaign_brief,
        "target_audience": req.target_audience,
        "offer": req.offer,
        "platform": req.platform,
        "tone": req.tone or "Professional, direct, and grounded",
        "research_insights": None,
        "messaging_angles": None,
        "copy_variants": None,
        "evaluation_scores": None,
        "evaluation_feedback": None,
        "approved": False,
        "human_approved": None,
        "human_feedback": None,
        "human_reject_reason": None,
        "human_reject_severity": None,
        "human_tags": None,
        "best_variant": None,
        "best_variant_score": None,
        "email_sequence": None,
        "revision_count": 0,
        "max_revisions": int(req.max_revisions),
        "metadata": {},
    }

    result = graph.invoke(state)

    email_sequence: List[EmailItem] = []
    raw_emails = result.get("email_sequence") or []
    for e in raw_emails:
        if not isinstance(e, dict):
            continue
        email_sequence.append(
            EmailItem(
                subject=str(e.get("subject", "")),
                body=str(e.get("body", "")),
                send_day=int(e.get("send_day", 0)),
            )
        )

    return CampaignResponse(
        best_variant=result.get("best_variant"),
        evaluation_scores=result.get("evaluation_scores"),
        best_variant_score=result.get("best_variant_score"),
        email_sequence=email_sequence,
        raw_state=result,
    )


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}