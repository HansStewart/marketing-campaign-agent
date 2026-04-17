import asyncio
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv
from langsmith import aevaluate
from langchain_openai import ChatOpenAI

# Ensure project root is on sys.path so we can import config, graph, etc.
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DEFAULT_MAX_REVISIONS, PLATFORM_TONE_MAP  # noqa: E402
from graph import build_graph  # noqa: E402

load_dotenv()

DATASET_NAME = "marketing-campaign-briefs-v1"
EXPERIMENT_PREFIX = "marketing-campaign-agent-v1"


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


def example_to_state(inputs: Dict[str, Any]) -> Dict[str, Any]:
    platform = inputs["platform"]
    tone = PLATFORM_TONE_MAP.get(platform, "Professional, modern, confident")

    return {
        "campaign_brief": inputs["brief"],
        "target_audience": inputs["audience"],
        "offer": inputs["offer"],
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
        "max_revisions": DEFAULT_MAX_REVISIONS,
        "metadata": {
            "source": "scripts/evaluate_langsmith.py",
        },
    }


def summarize_output(outputs: Dict[str, Any]) -> str:
    best_variant = outputs.get("best_variant") or ""
    best_score = outputs.get("best_variant_score")
    platform = outputs.get("platform") or ""
    return (
        f"Platform: {platform}\n"
        f"Best score: {best_score}\n"
        f"Best variant:\n{best_variant}"
    )


judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


async def clarity_evaluator(
    outputs: Dict[str, Any],
    reference_outputs: Dict[str, Any],
) -> bool:
    prompt = (
        "You are grading campaign copy clarity.\n"
        "Return CORRECT if the best variant is clear, specific, and easy to understand.\n"
        "Return INCORRECT otherwise.\n\n"
        f"{summarize_output(outputs)}"
    )
    response = await judge_llm.ainvoke(prompt)
    return "CORRECT" in response.content.upper()


async def cta_evaluator(
    outputs: Dict[str, Any],
    reference_outputs: Dict[str, Any],
) -> bool:
    prompt = (
        "You are grading CTA quality in marketing copy.\n"
        "Return CORRECT if the best variant ends with a clear, low-friction CTA.\n"
        "Return INCORRECT otherwise.\n\n"
        f"{summarize_output(outputs)}"
    )
    response = await judge_llm.ainvoke(prompt)
    return "CORRECT" in response.content.upper()


def score_threshold_evaluator(outputs: Dict[str, Any]) -> bool:
    score = outputs.get("best_variant_score")
    return score is not None and score >= 8.0


async def main():
    validate_environment()

    app = build_graph()
    target = example_to_state | app

    results = await aevaluate(
        target,
        data=DATASET_NAME,
        evaluators=[
            clarity_evaluator,
            cta_evaluator,
            score_threshold_evaluator,
        ],
        max_concurrency=2,
        experiment_prefix=EXPERIMENT_PREFIX,
        metadata={
            "workflow": "marketing-campaign-agent",
            "mode": "auto-approve",
        },
    )

    print(results)


if __name__ == "__main__":
    asyncio.run(main())