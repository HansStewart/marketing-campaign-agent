import os
import sys

import pytest

# Add project root to sys.path so we can import state.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from state import CampaignState


def test_initial_state_keys():
    state = CampaignState(
        campaign_brief="test",
        target_audience="test",
        offer="test",
        platform="LinkedIn",
        tone="Professional",
        research_insights=None,
        messaging_angles=None,
        copy_variants=None,
        evaluation_scores=None,
        evaluation_feedback=None,
        approved=False,
        human_approved=None,
        human_feedback=None,
        best_variant=None,
        best_variant_score=None,
        revision_count=0,
        max_revisions=4,
        metadata={},
    )
    assert state["revision_count"] == 0
    assert state["approved"] is False