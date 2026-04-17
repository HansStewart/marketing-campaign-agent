# Marketing Campaign Agent

A LangGraph-based marketing campaign agent that generates campaign strategy, copy variants, evaluation scores, and follow-up email sequences for multiple channels.

## What it does

Given a campaign brief, audience, offer, platform, and tone, the agent:

1. Generates 3 research insights and 3 messaging angles
2. Writes 3 campaign copy variants
3. Evaluates and scores the variants
4. Selects the best-performing variant
5. Supports human review or auto-approve mode
6. Generates a 3-email follow-up sequence
7. Logs and evaluates runs with LangSmith

## Supported platforms

- LinkedIn
- Instagram
- Facebook
- Email

## Project structure

```text
marketing-campaign-agent/
├── .github/workflows/ci.yml
├── inputs/campaign_briefs.json
├── outputs/
├── scripts/
│   ├── __init__.py
│   ├── evaluate_langsmith.py
│   └── upload_dataset_to_langsmith.py
├── tests/
├── batch_run.py
├── config.py
├── graph.py
├── main.py
├── nodes.py
├── schemas.py
├── state.py
└── README.md
```

## Requirements

- Python 3.12+
- OpenAI API key
- LangSmith API key

## Environment setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_TRACING=true
```

## Install

```bash
python -m venv testenv
source testenv/bin/activate
pip install -r requirements.txt
```

On Windows Git Bash:

```bash
python -m venv testenv
source testenv/Scripts/activate
pip install -r requirements.txt
```

## Run a single campaign

```bash
python main.py --platform LinkedIn
```

## Run a batch of briefs

```bash
python batch_run.py
```

This reads from:

```text
inputs/campaign_briefs.json
```

and writes summaries to:

```text
outputs/
```

## Run tests and lint

```bash
ruff check .
pytest
```

## Upload dataset to LangSmith

```bash
python scripts/upload_dataset_to_langsmith.py
```

This creates or updates the dataset:

```text
marketing-campaign-briefs-v1
```

## Run LangSmith evaluation

```bash
python scripts/evaluate_langsmith.py
```

This evaluates the graph against the dataset using:
- clarity evaluator
- CTA evaluator
- score threshold evaluator

## CI

GitHub Actions runs:
- Ruff
- pytest
- LangSmith dataset upload
- LangSmith evaluation

Required GitHub repository secrets:
- `OPENAI_API_KEY`
- `LANGSMITH_API_KEY`

## Notes

- Use repository Actions secrets, not Codespaces secrets, for CI.
- Store only raw secret values in GitHub, not `KEY=value`.
- `.env` should stay local and never be committed.
- `.env.example` can be committed as a template.

## Current status

This repo is working end to end with:
- local generation
- batch execution
- structured human review
- LangSmith dataset upload
- LangSmith evaluation
- GitHub Actions CI

## Next improvements

- Add more dataset examples
- Tighten prompt quality based on evaluator feedback
- Add richer evaluators for subject line quality and platform fit
- Expand output formats for more channels