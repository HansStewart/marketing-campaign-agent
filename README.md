Marketing Campaign Agent – LangGraph · LangChain · Pydantic
------------------------------------------------------------

Overview

This repository contains a stateful AI workflow for generating and refining marketing campaign copy. The system is implemented as a graph of specialized agents using LangGraph for orchestration, LangChain for prompt and model abstraction, and Pydantic for strict output schemas.

Instead of a single prompt that returns one response, the workflow decomposes the task into distinct roles:

- Strategist: derives campaign insights and messaging angles
- Copywriter: produces multiple copy variants
- Evaluator: scores quality and decides whether to approve
- Finalizer: selects the best variant and exposes the output

The graph supports iterative improvement via evaluator‑driven revision loops and is designed to be extended with human‑in‑the‑loop checkpoints and external search tools.

High‑Level System Architecture
------------------------------

Execution Flow

1. Strategist node  
   Inputs: campaign brief, target audience, offer, platform, tone  
   Outputs: structured strategic insights and three messaging angles  
   Responsibility: transform a loose marketing ask into a clear strategic direction that downstream agents can use.

2. Copywriter node  
   Inputs: strategist outputs, campaign context, optional feedback from prior evaluations  
   Outputs: exactly three copy variants  
   Responsibility: generate high‑quality campaign copy aligned with the angles and platform, with strong hooks and clear calls to action.

3. Evaluator node  
   Inputs: campaign context and the three copy variants  
   Outputs: numeric scores for each variant, an approval decision, and detailed feedback  
   Responsibility: act as a creative director, enforce quality thresholds, and provide actionable revision guidance.

4. Finalizer node  
   Inputs: the best variant and its score  
   Outputs: a finalized campaign asset and a run summary  
   Responsibility: present the approved variant and summarize how the system arrived at it.

Graph Orchestration

The workflow is expressed as a directed graph with typed shared state. The core route is:

strategist → copywriter → evaluator → finalize

A conditional edge after the evaluator allows the graph to either finalize or loop back for revision:

- If at least one variant reaches or exceeds the approval score (for example, 8.0 out of 10.0), the graph routes to the finalizer.
- If quality is below threshold and the revision limit has not been reached, the graph routes back to the copywriter with the evaluator’s feedback.
- If the maximum number of revisions is reached, the system finalizes using the best available variant.

This design allows the workflow to behave more like a real creative process rather than a single one‑shot generation.

Role of Each Core Technology
----------------------------

LangGraph

LangGraph is responsible for representing and executing the workflow as a stateful graph. It manages node registration and execution order, conditional routing based on evaluation results, shared state propagation between nodes, and support for human‑in‑the‑loop pauses and resumptions.

LangChain

LangChain provides the model abstraction and compositional building blocks around the LLM. Prompt templates define the system and human messages for each node in a consistent way. Model invocation is encapsulated in simple chains, and structured output helpers connect model responses directly to Pydantic schemas.

Pydantic

Pydantic is used to define strict, typed schemas for each node’s outputs, such as strategy, copy, and evaluation results. Binding the LLM to these schemas enforces predictable structures instead of free‑form text, which removes fragile parsing code and makes downstream graph steps easier to maintain and extend.

Shared State Design
-------------------

The graph operates over a typed shared state object that includes:

- Campaign inputs: campaign_brief, target_audience, offer, platform, tone  
- Intermediate artifacts: research_insights, messaging_angles, copy_variants  
- Evaluation data: evaluation_scores, evaluation_feedback, approved  
- Final outputs: best_variant, best_variant_score  
- Control fields: revision_count, max_revisions  
- Metadata: a dictionary used to track which nodes have completed

Each node reads from and writes to this shared state, and conditional routing decisions are made based on it. This makes the workflow explicit and makes it easy to inspect or replay runs with different inputs.

Current Capabilities
--------------------

The system currently supports:

- Multi‑stage campaign generation running through a graph rather than a single prompt
- High‑level strategy derivation and messaging angle selection
- Generation of three distinct campaign copy options tailored to a platform and audience
- Evaluation of each variant with numeric scoring and approval logic
- One or more revision loops based on evaluator feedback, up to a configurable maximum
- Clean final output selection and run summary logging

The default configuration targets real estate agents in Dallas, promoting a 24/7 AI lead follow‑up system for LinkedIn campaigns, but the inputs can be adjusted to target other industries, offers, and channels.


Human‑In‑The‑Loop Review
------------------------

The workflow includes a human review checkpoint between the evaluator and the finalizer. The complete flow is:

strategist → copywriter → evaluator → human_review → finalize

The human review node:

- Presents the best variant and evaluation scores to a human reviewer.
- Accepts an approve or reject decision along with optional revision feedback.
- Routes accordingly: if approved, the graph proceeds to finalize; if rejected, the human feedback is attached to shared state and the graph routes back to the copywriter for another revision cycle.
- Respects the max_revisions guardrail, which forces finalization if the revision limit is reached regardless of human approval status.

This pattern mirrors real creative and compliance workflows where AI can draft and iterate, but humans retain control over what is ultimately published. It demonstrates LangGraph's pause‑and‑resume capability as a first‑class orchestration feature.

Project Structure
-----------------

Top‑level layout:

marketing-campaign-agent  
  .env  
  state.py  
  schemas.py  
  nodes.py  
  graph.py  
  main.py  
  README.md  

state.py defines the typed shared state for the graph.  
schemas.py defines Pydantic models for structured outputs.  
nodes.py implements the strategist, copywriter, evaluator, and finalizer nodes.  
graph.py defines the LangGraph graph, nodes, and conditional routing.  
main.py initializes the graph, seeds the initial state, and runs a sample campaign.  
.env stores API keys and configuration values loaded at runtime.

Execution and Example Output
----------------------------

Running the entrypoint script launches a full campaign generation run. A typical run produces:

- an approval decision  
- a revision count  
- a list of scores for each variant  
- the best score and corresponding copy  
- metadata indicating which nodes completed

The console summary shows the final approved variant and the numeric evaluation backing that decision, demonstrating the system’s ability to reason over multiple options and select the best one instead of returning the first draft.

Rationale
---------

The project is designed to demonstrate:

- graph‑based orchestration for agent workflows  
- clear separation between orchestration, model interaction, and data validation  
- evaluator‑driven feedback loops and revision logic  
- realistic marketing‑campaign behavior grounded in a specific business use case

It serves as a reusable pattern for building stateful AI workflows around strategy, content generation, and automated quality control.

## Setup

1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/Scripts/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root

```env
OPENAI_API_KEY=your_openai_api_key_here
```

4. Run the app

```bash
python main.py
```

## Usage

Run the app:

```bash
python main.py
```

When you see:

```text
Decision - approve or reject? (a/r):
```

Type:

- `a` to approve the selected variant
- `r` to reject it