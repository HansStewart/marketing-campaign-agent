# Marketing Campaign Agent (LangChain + LangGraph + LangSmith)

An AI-powered marketing campaign agent built with **LangChain**, **LangGraph**, and **LangSmith**.  
It generates, evaluates, and human‑reviews multi-step campaign copy (e.g., LinkedIn/Instagram/Facebook/Email) for real estate lead follow-up.

---

## Features

- **Multi-step agent workflow** using LangGraph:
  - Strategist → Copywriter → Evaluator → Human Review → Finalize
- **LLM-powered nodes** built with LangChain:
  - `ChatOpenAI` (GPT‑4o‑mini) and `ChatPromptTemplate`
  - Structured outputs for strategy, copy, and evaluation
- **Human‑in‑the‑loop review**:
  - CLI prompt to approve/reject the best variant and provide revision feedback
- **Multi-platform support** via config and CLI:
  - `LinkedIn`, `Instagram`, `Facebook`, `Email` with platform‑specific tone
- **Observability with LangSmith**:
  - Full LangGraph run tracing (nodes, prompts, tokens, latency) in the LangSmith UI
- **Developer ergonomics**:
  - `.env`‑based secret management
  - `python-dotenv` for local development
  - `ruff` linting + `pytest` tests
  - Run outputs saved to `outputs/*.json`

---

## Tech Stack

- **Python** 3.11+
- **LangChain** – prompt and LLM building blocks (`langchain_openai`, `langchain_core`)
- **LangGraph** – stateful agent graph orchestration
- **LangSmith** – tracing and observability
- **OpenAI** – GPT‑4o‑mini via `openai` + `langchain_openai`
- **Tooling** – `pytest`, `ruff`, `python-dotenv`

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/HansStewart/marketing-campaign-agent.git
cd marketing-campaign-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash / PowerShell
# or: source venv/bin/activate  # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment variables

Create a `.env` file in the project root (same folder as `main.py`) with:

```env
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=marketing-campaign-agent
```

For safety, the repo includes an example file:

```env
# .env.example
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=marketing-campaign-agent
```

Copy this template and fill in your real keys for local use only.

---

## Usage

From the project root (with the virtualenv activated):

```bash
python main.py
```

You’ll see the agent run through strategist, copywriter, and evaluator nodes, then pause for human input:

```text
HUMAN REVIEW REQUIRED
...
Decision — approve or reject? (a/r):
```

Type:

- `a` to approve the best variant
- `r` to reject and provide revision feedback

After approval, the agent prints a run summary and saves the result to `outputs/run-YYYYMMDD-HHMMSS.json`.

---

## CLI Options

You can customize the campaign without editing code using CLI arguments:

```bash
python main.py --help
```

Example:

```bash
python main.py \
  --platform Instagram \
  --audience "Real estate investors in Austin, Texas" \
  --offer "AI follow-up that nurtures leads across SMS and email"
```

Arguments:

- `--platform` – one of `LinkedIn`, `Instagram`, `Facebook`, `Email`
- `--audience` – target audience description
- `--offer` – campaign offer description
- `--brief` (if enabled) – full campaign brief text

Platform‑specific tone is configured in `config.py`.

---

## How It Works (Architecture)

The agent is implemented as a **LangGraph state machine**:

1. **Strategist node (`strategist_node`)**
   - Uses LangChain `ChatPromptTemplate` + `ChatOpenAI`
   - Generates research insights and 3 differentiated messaging angles

2. **Copywriter node (`copywriter_node`)**
   - Writes 3 campaign copy variants based on the brief, angles, and prior feedback
   - Enforces strict style rules (no exclamation marks, realistic tone, B2B focus)

3. **Evaluator node (`evaluator_node`)**
   - Scores each variant across multiple dimensions (hook, clarity, relevance, offer, CTA)
   - Picks the best variant and decides whether to approve or request revision

4. **Human Review node (`human_review_node`)**
   - Displays the best variant and scores in the terminal
   - Lets you approve (`a`) or reject (`r`) with feedback

5. **Finalize node (`finalize_node`)**
   - Prints a summary and marks the run as finalized

The graph orchestration is defined in `graph.py`, state shape in `state.py`, and structured outputs in `schemas.py`.

---

## Observability with LangSmith

This project is instrumented for LangSmith tracing:

- Every run appears as a LangGraph trace in the LangSmith UI.
- You can inspect:
  - Input/output for each node
  - LLM prompts and responses
  - Tokens, latency, and errors (if any)
- Project name: `marketing-campaign-agent` (configured via `LANGSMITH_PROJECT`)

To view traces:

1. Go to https://smith.langchain.com
2. Open the `marketing-campaign-agent` project
3. Click into a run to see the full node tree and details

---

### What you see in LangSmith

Each run appears as a LangGraph trace with child nodes:

- `strategist` – LangChain prompt + GPT‑4o‑mini call for research & angles
- `copywriter` – LangChain prompt + GPT‑4o‑mini call for 3 copy variants
- `evaluator` – LangChain prompt + GPT‑4o‑mini call for scoring/selection
- `human_review` – human decision and feedback captured in state
- `finalize` – summary and final metadata

This makes it clear that:
- **LangChain** powers the LLM calls and prompts,
- **LangGraph** orchestrates the node flow,
- **LangSmith** traces the entire workflow for debugging and optimization.

## Development

### Linting

```bash
ruff check .
```

### Tests

```bash
pytest
```

Example tests:

- `tests/test_smoke.py` – ensures `CampaignState` initializes correctly and keys behave as expected.

### Configuration

All configurable defaults live in `config.py`:

- `MODEL_NAME`, `MODEL_TEMPERATURE`
- `DEFAULT_MAX_REVISIONS`, `DEFAULT_PLATFORM`, `DEFAULT_LOCATION`
- `SUPPORTED_PLATFORMS`, `PLATFORM_TONE_MAP`

---

## Project Status

This repo currently demonstrates:

- ✅ LangChain for LLM, prompts, and structured outputs
- ✅ LangGraph for multi-node agent workflows
- ✅ LangSmith for full tracing and observability
- ✅ Multi-platform campaign support via CLI and config
- ✅ Clean code via `ruff` and `pytest`

Planned enhancements:

- Additional campaign types (email sequences, ads, landing page copy)
- More robust evaluation metrics
- Deeper testing for each node and edge cases

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.