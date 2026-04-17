import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.evaluate_langsmith import example_to_state  # noqa: E402


def test_example_to_state_maps_inputs_correctly():
    inputs = {
        "platform": "LinkedIn",
        "audience": "Test audience",
        "offer": "Test offer",
        "brief": "Test brief",
    }

    state = example_to_state(inputs)

    assert state["platform"] == "LinkedIn"
    assert state["target_audience"] == "Test audience"
    assert state["offer"] == "Test offer"
    assert state["campaign_brief"] == "Test brief"
    assert state["auto_approve"] is True