from datetime import datetime, timezone

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

DATASET_NAME = "marketing-campaign-briefs-v1"
TAG_NAME = "v1"


def main():
    client = Client()
    now = datetime.now(timezone.utc)

    client.update_dataset_tag(
        dataset_name=DATASET_NAME,
        as_of=now,
        tag=TAG_NAME,
    )

    print(f"Tagged dataset '{DATASET_NAME}' with tag '{TAG_NAME}' at {now.isoformat()}")


if __name__ == "__main__":
    main()