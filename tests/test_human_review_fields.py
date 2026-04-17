import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from state import CampaignState  # noqa: E402


def test_campaign_state_accepts_structured_human_review_fields():
    state: CampaignState = {
        "campaign_brief": "Test brief",
        "target_audience": "Test audience",
        "offer": "Test offer",
        "platform": "LinkedIn",
        "tone": "Professional",
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
        "max_revisions": 4,
        "metadata": {},
    }

    assert "human_reject_reason" in state
    assert "human_reject_severity" in state
    assert "human_tags" in state