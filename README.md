# Marketing Campaign Agent

A LangGraph-based workflow for generating and evaluating multi-channel B2B marketing campaigns. The agent takes a structured brief, creates strategy and copy variants, scores them, supports optional human review, and produces a three-email follow-up sequence. It is instrumented with LangSmith for tracing and evaluation and wired into GitHub Actions for continuous testing and quality checks.

---

## Capabilities

### Strategy Generation
- Produces three concise research insights about the target audience and offer
- Produces three distinct messaging angles, each targeting a different pain point or outcome

### Copy Generation
- Writes three campaign copy variants adapted to a specific platform and tone
- Enforces constraints on length, style, and banned generic phrases
- Tailors hooks and CTAs for LinkedIn, Instagram, Facebook, and Email

### Evaluation and Selection
- Scores each variant on hook strength, clarity, relevance, offer presentation, and CTA quality
- Computes one overall score per variant
- Selects the best-performing variant and flags whether it should be auto-approved

### Human-in-the-Loop Review
- Optional pause for a human to approve or reject the best variant
- Captures structured rejection data:
  - `human_reject_reason` — hook, clarity, relevance, offer, cta, or other
  - `human_reject_severity` — low, med, or high
  - `human_tags` — free-form tags such as `too-long`, `weak-cta`, `generic`
- Captures free-text `human_feedback` to guide the next revision

### Email Follow-Up Sequence
- Generates a three-email sequence based on the approved best variant
- Enforces send days of 1, 3, and 7
- Subject lines under seven words, no exclamation marks, no hashtags
- Body length between 60 and 120 words per email
- One clear, low-friction CTA per email
- Adapts tone and voice to the originating platform and audience

### Batch Processing
- Runs a batch of predefined campaign briefs from a JSON file
- Executes the full workflow for each brief without requiring human input
- Writes structured summaries to the `outputs/` directory

### LangSmith Integration
- Uploads the brief dataset to LangSmith as a named, versioned dataset
- Evaluates the graph against the dataset using multiple evaluators
- Streams evaluation progress and prints the experiment URL for inspection

### Continuous Integration
- GitHub Actions workflow runs on every push
- Executes linting, tests, dataset upload, and LangSmith evaluation
- Ensures all changes are checked automatically

---

## Repository Layout

```text
marketing-campaign-agent/
├── .github/
│   └── workflows/
│       └── ci.yml
├── inputs/
│   └── campaign_briefs.json
├── outputs/
├── scripts/
│   ├── __init__.py
│   ├── upload_dataset_to_langsmith.py
│   ├── evaluate_langsmith.py
│   └── tag_dataset_version.py
├── tests/
├── batch_run.py
├── config.py
├── graph.py
├── nodes.py
├── schemas.py
├── state.py
├── AGENTS.md
└── README.md
```

---

## Core Data Flow

```text
Input State
    │
    ▼
Strategist Node
    │  research_insights, messaging_angles
    ▼
Copywriter Node
    │  copy_variants
    ▼
Evaluator Node
    │  evaluation_scores, best_variant, best_variant_score
    ▼
Human Review Node (optional)
    │  human_approved, human_feedback, human_reject_reason,
    │  human_reject_severity, human_tags
    ▼
Email Sequence Node
    │  email_sequence (3 emails, send days 1, 3, 7)
    ▼
Finalize Node
    │  run summary printed to console
    ▼
Output State
```

---

## Setup

### Prerequisites
- Python 3.12 or later
- OpenAI API key
- LangSmith API key and workspace

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_TRACING=true
```

Do not commit `.env`. Use `.env.example` to document variables for others.

### Installation

**macOS or Linux:**
```bash
python -m venv testenv
source testenv/bin/activate
pip install -r requirements.txt
```

**Windows PowerShell:**
```powershell
python -m venv testenv
testenv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Git Bash (Windows):**
```bash
python -m venv testenv
source testenv/Scripts/activate
pip install -r requirements.txt
```

---

## Usage

### Single Run

```bash
python main.py --platform LinkedIn
```

The graph will generate insights and messaging angles, produce three copy variants, evaluate and select the best one, and generate a three-email follow-up sequence. Output is printed to the console.

### Batch Run

```bash
python batch_run.py
```

Reads from `inputs/campaign_briefs.json` and writes structured output summaries to `outputs/`.

**Input format:**
```json
[
  {
    "label": "linkedin-real-estate-dallas",
    "platform": "LinkedIn",
    "audience": "Dallas real estate agents",
    "offer": "AI lead follow-up system",
    "brief": "Help agents respond to leads in under 60 seconds."
  }
]
```

---

## Testing and Linting

```bash
ruff check .
pytest
```

Tests cover CLI defaults, platform-specific styles and tones, auto-approve behavior, batch runner shape, structured human review fields, and LangSmith dataset mapping.

---

## LangSmith Integration

### Upload Dataset

```bash
python scripts/upload_dataset_to_langsmith.py
```

Creates or refreshes the dataset `marketing-campaign-briefs-v1` in LangSmith using examples from `inputs/campaign_briefs.json`.

### Tag Dataset Version

```bash
python scripts/tag_dataset_version.py
```

Tags the current dataset state as `v1`, anchoring a stable evaluation baseline.

### Run Evaluation

```bash
python scripts/evaluate_langsmith.py
```

Runs the graph against the dataset using three evaluators:
- Clarity evaluator
- CTA evaluator
- Score threshold evaluator

Prints the experiment URL and streams run summaries to the console. If the run is long, it is safe to stop with `Ctrl+C`. Completed runs and scores remain in LangSmith.

---

## Continuous Integration

The workflow is defined in `.github/workflows/ci.yml` and runs on every push to `main`.

**Steps:**
1. Check out repository
2. Set up Python
3. Install dependencies
4. Run Ruff
5. Run pytest
6. Upload or refresh LangSmith dataset
7. Run LangSmith evaluation

**Required GitHub repository secrets:**

| Secret Name | Value Format |
|---|---|
| `OPENAI_API_KEY` | `sk-...` |
| `LANGSMITH_API_KEY` | `lsv2_...` |

Configure these under **Repository Settings → Secrets and variables → Actions**. Store raw key values only — do not include `KEY=` in the value field.

---

## Campaign State Reference

| Field | Type | Description |
|---|---|---|
| `campaign_brief` | str | Core brief input |
| `target_audience` | str | Audience description |
| `offer` | str | What is being offered |
| `platform` | str | LinkedIn, Instagram, Facebook, Email |
| `tone` | str | Tone and voice direction |
| `research_insights` | list | Three audience or market insights |
| `messaging_angles` | list | Three distinct positioning angles |
| `copy_variants` | list | Three generated copy options |
| `evaluation_scores` | list | Float score per variant |
| `evaluation_feedback` | str | Short evaluator summary |
| `approved` | bool | Auto-approval flag |
| `human_approved` | bool or None | Human decision |
| `human_feedback` | str or None | Human revision notes |
| `human_reject_reason` | str or None | Structured rejection reason |
| `human_reject_severity` | str or None | low, med, or high |
| `human_tags` | list or None | Free-form rejection tags |
| `best_variant` | str or None | Selected best copy |
| `best_variant_score` | float or None | Score of best variant |
| `email_sequence` | list or None | Three follow-up emails |
| `revision_count` | int | Number of revision cycles |
| `max_revisions` | int | Maximum allowed revisions |
| `metadata` | dict | Completion flags and audit data |

---

## Contributor and Agent Guidance

See `AGENTS.md` for detailed guidance on how to work safely in this codebase.

Key rules:
- Keep `state.py`, `schemas.py`, and node logic in sync at all times
- When you change prompts, rerun lint, tests, and at least one evaluation run
- Preserve structured output field names and types
- Use full-file replacements for complex changes to reduce drift risk

---

## Roadmap

- Expand the brief dataset with more verticals and platforms
- Add evaluators for subject line quality, platform fit, and tone compliance
- Add CLI flags to evaluate on a dataset subset for faster local iteration
- Introduce configuration files for model selection and temperature per node
- Provide richer export formats such as CSV or HTML reports
- Expand human review to capture positive feedback signals, not only rejections

---

## v1.0.0 Release Notes

This is the initial stable release. The core workflow, batch runner, human review loop, LangSmith integration, and CI pipeline are all functional and tested.