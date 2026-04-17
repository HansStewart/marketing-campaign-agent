import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from graph import route_after_evaluation  # noqa: E402


def test_route_after_evaluation_goes_to_email_sequence_when_auto_approve_enabled():
    state = {
        "approved": True,
        "auto_approve": True,
        "revision_count": 0,
        "max_revisions": 4,
    }
    assert route_after_evaluation(state) == "email_sequence"


def test_route_after_evaluation_goes_to_human_review_when_auto_approve_disabled():
    state = {
        "approved": True,
        "auto_approve": False,
        "revision_count": 0,
        "max_revisions": 4,
    }
    assert route_after_evaluation(state) == "human_review"


def test_route_after_evaluation_returns_copywriter_when_not_approved_and_revisions_remain():
    state = {
        "approved": False,
        "auto_approve": True,
        "revision_count": 1,
        "max_revisions": 4,
    }
    assert route_after_evaluation(state) == "copywriter"