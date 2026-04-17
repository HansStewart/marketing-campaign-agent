import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.upload_dataset_to_langsmith import build_examples  # noqa: E402


def test_build_examples_returns_expected_langsmith_shape():
    briefs = [
        {
            "label": "test-brief",
            "platform": "Email",
            "audience": "Test audience",
            "offer": "Test offer",
            "brief": "Test brief",
        }
    ]

    examples = build_examples(briefs)

    assert len(examples) == 1
    assert examples[0]["inputs"]["platform"] == "Email"
    assert examples[0]["inputs"]["brief"] == "Test brief"
    assert examples[0]["outputs"]["label"] == "test-brief"
    assert examples[0]["metadata"]["source"] == "inputs/campaign_briefs.json"