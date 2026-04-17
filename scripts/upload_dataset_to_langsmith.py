import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

INPUT_PATH = Path("inputs/campaign_briefs.json")
DATASET_NAME = "marketing-campaign-briefs-v1"
DATASET_DESCRIPTION = (
    "Campaign brief dataset for evaluating the marketing campaign agent "
    "across LinkedIn, Instagram, Facebook, and Email use cases."
)


def validate_environment():
    required_keys = [
        "LANGSMITH_API_KEY",
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

    return data


def get_or_create_dataset(client: Client, dataset_name: str):
    existing = list(client.list_datasets(dataset_name=dataset_name))
    if existing:
        return existing[0]
    return client.create_dataset(
        dataset_name=dataset_name,
        description=DATASET_DESCRIPTION,
    )


def build_examples(briefs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    examples = []

    for item in briefs:
        examples.append(
            {
                "inputs": {
                    "platform": item["platform"],
                    "audience": item["audience"],
                    "offer": item["offer"],
                    "brief": item["brief"],
                },
                "outputs": {
                    "label": item.get("label"),
                },
                "metadata": {
                    "label": item.get("label"),
                    "source": "inputs/campaign_briefs.json",
                },
            }
        )

    return examples


def main():
    validate_environment()

    client = Client()
    briefs = load_briefs(INPUT_PATH)
    dataset = get_or_create_dataset(client, DATASET_NAME)
    examples = build_examples(briefs)

    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )

    print(f"Dataset ready: {dataset.name}")
    print(f"Dataset id: {dataset.id}")
    print(f"Examples uploaded: {len(examples)}")


if __name__ == "__main__":
    main()