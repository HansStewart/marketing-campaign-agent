# AGENTS.md

This file explains how AI coding agents should work in this repository.

## Project goal

This repository contains a LangGraph-based marketing campaign generation and evaluation workflow. The system creates campaign assets, scores them, supports human review, and runs LangSmith evaluations locally and in CI.

## Key files

- `main.py` — single campaign CLI entrypoint
- `batch_run.py` — batch runner for multiple briefs
- `graph.py` — LangGraph wiring
- `nodes.py` — LangGraph node logic
- `schemas.py` — structured outputs
- `state.py` — graph state definition
- `scripts/upload_dataset_to_langsmith.py` — dataset upload script
- `scripts/evaluate_langsmith.py` — evaluation script
- `tests/` — test suite

## Working rules

- Always preserve structured output contracts in `schemas.py`
- Keep graph state fields synchronized with `state.py`
- When changing prompts in `nodes.py`, rerun:
  - `ruff check .`
  - `pytest`
  - `python scripts/evaluate_langsmith.py`
- Do not commit `.env`
- Do commit `.env.example` when environment requirements change
- Prefer full-file replacements when making surgical changes that affect prompts or workflow logic
- Keep prompts concise and explicit
- Avoid introducing placeholder text in generated campaign assets

## CI expectations

GitHub Actions should remain green for:
- lint
- tests
- LangSmith dataset upload
- LangSmith evaluation

## LangSmith notes

- Dataset name: `marketing-campaign-briefs-v1`
- Dataset changes create new versions automatically
- Use dataset tags for important milestones
- Use evaluation runs to compare prompt changes over time

## Documentation expectations

When updating docs:
- keep setup instructions exact
- prefer runnable commands over abstract explanations
- document required secrets clearly
- keep README aligned with actual code and workflow behavior