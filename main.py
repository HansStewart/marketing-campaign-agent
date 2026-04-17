import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

from graph import build_graph


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


def run_campaign_agent():
    validate_environment()

    app = build_graph()

    initial_state = {
        "campaign_brief": "Create a high-converting campaign promoting an AI lead follow-up system for real estate agents.",
        "target_audience": "Real estate agents and small real estate teams in Dallas, Texas",
        "offer": "A 24/7 AI lead follow-up system that responds in under 60 seconds and books appointments automatically",
        "platform": "LinkedIn",
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
        "max_revisions": 4,
        "metadata": {},
    }

    result = app.invoke(initial_state)

    print("Run complete.")
    print(f"Approved by evaluator:  {result.get('approved')}")
    print(f"Approved by human:      {result.get('human_approved')}")
    print(f"Revision count:         {result.get('revision_count')}")
    print(f"Scores:                 {result.get('evaluation_scores')}")
    print(f"Metadata:               {result.get('metadata')}")

    return result


if __name__ == "__main__":
    run_campaign_agent()