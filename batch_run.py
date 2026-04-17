import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from config import DEFAULT_MAX_REVISIONS, PLATFORM_TONE_MAP
from graph import build_graph

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

INPUT_PATH = Path("inputs/campaign_briefs.json")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def validate_environment():
    required_keys = [
        "OPENAI_API_KEY",
        "LANGSMITH_API_KEY",
        "LANGSMITH_TRACING",
    ]

    missing = [key for key in required_keys if not os.getenv(key)]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def load_briefs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of campaign brief objects")

    required_fields = {"platform", "audience", "offer", "brief"}

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item {index} must be an object")
        missing = required_fields - set(item.keys())
        if missing:
            raise ValueError(
                f"Item {index} is missing required fields: {', '.join(sorted(missing))}"
            )

    return data


def make_initial_state(item: Dict[str, Any]) -> Dict[str, Any]:
    platform = item["platform"]
    tone = PLATFORM_TONE_MAP.get(platform, "Professional, modern, confident")

    return {
        "campaign_brief": item["brief"],
        "target_audience": item["audience"],
        "offer": item["offer"],
        "platform": platform,
        "tone": tone,
        "research_insights": None,
        "messaging_angles": None,
        "copy_variants": None,
        "evaluation_scores": None,
        "evaluation_feedback": None,
        "approved": False,
        "auto_approve": True,
        "human_approved": None,
        "human_feedback": None,
        "human_reject_reason": None,
        "human_reject_severity": None,
        "human_tags": None,
        "best_variant": None,
        "best_variant_score": None,
        "email_sequence": None,
        "revision_count": 0,
        "max_revisions": item.get("max_revisions", DEFAULT_MAX_REVISIONS),
        "metadata": {
            "batch_label": item.get("label"),
            "source": "batch_run.py",
        },
    }


def summarize_result(item: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "label": item.get("label"),
        "platform": item["platform"],
        "audience": item["audience"],
        "offer": item["offer"],
        "brief": item["brief"],
        "approved": result.get("approved"),
        "auto_approve": result.get("auto_approve"),
        "human_approved": result.get("human_approved"),
        "revision_count": result.get("revision_count"),
        "best_variant_score": result.get("best_variant_score"),
        "evaluation_scores": result.get("evaluation_scores"),
        "best_variant": result.get("best_variant"),
        "email_sequence_count": len(result.get("email_sequence") or []),
        "metadata": result.get("metadata"),
    }


def save_batch_summary(results: List[Dict[str, Any]]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUTPUT_DIR / f"batch-run-{timestamp}.json"
    path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    logger.info("Batch summary saved to %s", path)
    return path


def run_batch():
    validate_environment()
    briefs = load_briefs(INPUT_PATH)
    app = build_graph()

    summaries = []

    logger.info("Starting batch run with %s briefs", len(briefs))

    for index, item in enumerate(briefs, start=1):
        label = item.get("label", f"brief-{index}")
        logger.info(
            "Running batch item %s/%s — %s (%s)",
            index,
            len(briefs),
            label,
            item["platform"],
        )

        initial_state = make_initial_state(item)
        result = app.invoke(initial_state)
        summary = summarize_result(item, result)
        summaries.append(summary)

        logger.info(
            "Completed %s — best score: %s, emails: %s",
            label,
            summary.get("best_variant_score"),
            summary.get("email_sequence_count"),
        )

    save_batch_summary(summaries)
    return summaries


if __name__ == "__main__":
    run_batch()