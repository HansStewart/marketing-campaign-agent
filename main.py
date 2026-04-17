import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from config import DEFAULT_LOCATION, DEFAULT_MAX_REVISIONS, DEFAULT_PLATFORM
from graph import build_graph

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def validate_environment():
    required_keys = [
        "OPENAI_API_KEY",
        "LANGCHAIN_API_KEY",
    ]

    missing = [key for key in required_keys if not os.getenv(key)]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the marketing campaign agent")
    parser.add_argument(
        "--platform",
        default=DEFAULT_PLATFORM,
        help="Target platform (default: LinkedIn)",
    )
    parser.add_argument(
        "--audience",
        default=f"Real estate agents and small real estate teams in {DEFAULT_LOCATION}",
        help="Target audience description",
    )
    parser.add_argument(
        "--offer",
        default="A 24/7 AI lead follow-up system that responds in under 60 seconds and books appointments automatically",
        help="Campaign offer description",
    )
    return parser.parse_args()


def save_run(result: dict) -> None:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUTPUT_DIR / f"run-{timestamp}.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    logger.info("Run saved to %s", path)


def run_campaign_agent():
    validate_environment()
    args = parse_args()

    app = build_graph()

    initial_state = {
        "campaign_brief": "Create a high-converting campaign promoting an AI lead follow-up system for real estate agents.",
        "target_audience": args.audience,
        "offer": args.offer,
        "platform": args.platform,
        "tone": "Professional, modern, confident, conversion-focused",
        "research_insights": None,
        "messaging_angles": None,
        "copy_variants": None,
        "evaluation_scores": None,
        "evaluation_feedback": None,
        "approved": False,
        "human_approved": None,
        "human_feedback": None,
        "best_variant": None,
        "best_variant_score": None,
        "revision_count": 0,
        "max_revisions": DEFAULT_MAX_REVISIONS,
        "metadata": {},
    }

    result = app.invoke(initial_state)

    logger.info("Run complete.")
    logger.info("Approved by evaluator:  %s", result.get("approved"))
    logger.info("Approved by human:      %s", result.get("human_approved"))
    logger.info("Revision count:         %s", result.get("revision_count"))
    logger.info("Scores:                 %s", result.get("evaluation_scores"))
    logger.info("Metadata:               %s", result.get("metadata"))

    save_run(result)

    return result


if __name__ == "__main__":
    run_campaign_agent()