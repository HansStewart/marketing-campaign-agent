import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from batch_run import load_briefs, make_initial_state, summarize_result  # noqa: E402


def test_load_briefs_reads_valid_json_list(tmp_path):
    data = [
        {
            "label": "test-brief",
            "platform": "LinkedIn",
            "audience": "Test audience",
            "offer": "Test offer",
            "brief": "Test brief",
        }
    ]
    path = tmp_path / "campaign_briefs.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    briefs = load_briefs(path)

    assert isinstance(briefs, list)
    assert briefs[0]["platform"] == "LinkedIn"


def test_make_initial_state_sets_auto_approve_true():
    item = {
        "label": "test-brief",
        "platform": "Email",
        "audience": "Test audience",
        "offer": "Test offer",
        "brief": "Test brief",
    }

    state = make_initial_state(item)

    assert state["auto_approve"] is True
    assert state["platform"] == "Email"
    assert state["campaign_brief"] == "Test brief"
    assert state["metadata"]["source"] == "batch_run.py"


def test_summarize_result_returns_expected_keys():
    item = {
        "label": "test-brief",
        "platform": "LinkedIn",
        "audience": "Test audience",
        "offer": "Test offer",
        "brief": "Test brief",
    }
    result = {
        "approved": True,
        "auto_approve": True,
        "human_approved": None,
        "revision_count": 0,
        "best_variant_score": 8.5,
        "evaluation_scores": [8.0, 8.5, 7.5],
        "best_variant": "Test variant",
        "email_sequence": [{"subject": "A"}, {"subject": "B"}, {"subject": "C"}],
        "metadata": {"source": "batch_run.py"},
    }

    summary = summarize_result(item, result)

    assert summary["label"] == "test-brief"
    assert summary["email_sequence_count"] == 3
    assert summary["best_variant_score"] == 8.5
    assert summary["metadata"]["source"] == "batch_run.py"


def test_load_briefs_raises_for_missing_required_fields(tmp_path):
    data = [
        {
            "label": "bad-brief",
            "platform": "LinkedIn",
            "audience": "Test audience",
            "brief": "Missing offer field",
        }
    ]
    path = tmp_path / "campaign_briefs.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    try:
        load_briefs(path)
        assert False, "Expected ValueError for missing required fields"
    except ValueError as exc:
        assert "missing required fields" in str(exc).lower()


def test_load_briefs_raises_for_non_list_json(tmp_path):
    path = tmp_path / "campaign_briefs.json"
    path.write_text(json.dumps({"platform": "LinkedIn"}), encoding="utf-8")

    try:
        load_briefs(path)
        assert False, "Expected ValueError for non-list JSON"
    except ValueError as exc:
        assert "must be a list" in str(exc).lower()