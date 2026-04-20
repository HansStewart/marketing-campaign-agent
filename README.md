Marketing Campaign Agent

An AI-powered marketing copy generation agent built on FastAPI, LangGraph, and OpenAI GPT-4o,
with full observability through LangSmith. Enter your platform, audience, and offer — the agent
runs a structured 4-node state graph to generate scored copy variants, evaluate each one, and
optionally produce a complete 3-email nurture sequence.

---

HOW THE AGENT WORKS

The agent is orchestrated using LangGraph — a stateful graph framework built on top of LangChain
that routes data through discrete, typed nodes connected by edges. Each request to the /generate
endpoint compiles and invokes a StateGraph that flows through four sequential nodes.

Every node receives the full CampaignState object, performs its task, and passes an updated state
to the next node. This architecture makes the pipeline modular, inspectable, and easy to extend.


THE LANGGRAPH PIPELINE

  Node 1 — copywrite_node
  Receives the full campaign context: platform, audience, offer, brief, persona data, tone, output
  formats, and brand file context. Constructs a structured system prompt and invokes GPT-4o via a
  LangChain LCEL chain (ChatPromptTemplate | ChatOpenAI | StrOutputParser). Returns raw copy output
  containing one or more variants separated by VARIANT delimiters.

  Node 2 — parse_node
  Splits the raw output on VARIANT delimiters using regex. Each variant is isolated as a standalone
  string and stored in the state as an array for independent evaluation in the next node.

  Node 3 — score_node
  Iterates over every parsed variant and runs a separate scoring chain for each. The scoring prompt
  instructs GPT-4o to evaluate the copy on five dimensions: hook strength, clarity, CTA effectiveness,
  tone match, and absence of hype. Each variant receives a score from 0.0 to 1.0 and a one-sentence
  reasoning statement. The highest-scoring variant is selected as the recommended output.

  Node 4 — email_node
  Runs conditionally — only when the platform is email or email is included in output formats.
  Generates a structured 3-email nurture sequence: awareness (Email 1), value and proof (Email 2),
  and CTA with urgency (Email 3). Output is parsed into structured JSON with subject, body, and
  send_day fields per email.

Graph edges:
  START -> copywrite_node -> parse_node -> score_node -> email_node -> END


LANGSMITH OBSERVABILITY

LangSmith is integrated as the tracing and observability layer. Every node in the graph is decorated
with @traceable, and every LangChain chain execution is captured automatically when
LANGCHAIN_TRACING_V2 is enabled.

For each run, LangSmith records:

  Full trace tree       Every node input and output captured as a nested span hierarchy
  Token usage           Input tokens, output tokens, and total cost per LangChain call
  Latency               Time-to-first-token and full completion time per node
  Prompt inspection     Exact prompts and completions sent to and received from the model
  Error capture         Failed nodes logged with full context and stack trace
  Run comparison        Compare outputs across prompt versions, models, or temperature settings
  Production monitoring Catch quality regressions without touching the codebase

LangSmith is optional. The agent runs without it if LANGCHAIN_API_KEY is not set. To enable full
tracing, add your LangSmith API key and set LANGCHAIN_TRACING_V2=true in your .env file.

Traces are visible at: https://smith.langchain.com under your project name marketing-campaign-agent.


FEATURES

Multi-Variant Generation
Generates 3 distinct copy variants per request written specifically for the platform, audience,
and offer provided. Every variant follows direct-response principles: hook, body, and specific CTA.

Automated Scoring
Each variant is scored 0.0 to 1.0 across five dimensions with a one-sentence reasoning statement.
The highest-scoring variant is surfaced automatically as the recommended output.

Structured Refinement Engine
Select any variant and refine it using labeled instruction sections:
  Change   — what to rewrite
  Keep     — what to preserve verbatim
  Tone     — tone direction
  Length   — word or sentence target
  CTA      — specific call-to-action rewrite
  Note     — additional constraints

Email Sequence Generator
When the platform is email or email is selected as an output format, the agent generates a
3-email nurture sequence parsed into structured JSON with subject line, body, and send day per email.

File Context Upload
Upload a .txt or .md brand brief up to 8,000 characters. The content is injected into the
copywriting node as brand context.

Campaign History
The last 50 campaigns are stored in session and accessible through the history panel.


TECH STACK

Backend          FastAPI, Python 3.10+
Agent Framework  LangGraph (StateGraph, typed nodes, compiled graph)
AI Chains        LangChain LCEL (ChatPromptTemplate, ChatOpenAI, StrOutputParser)
LLM              OpenAI GPT-4o
Observability    LangSmith (traceable decorators, distributed tracing, token monitoring)
Frontend         Next.js, React, TypeScript
Environment      python-dotenv


GETTING STARTED

Prerequisites
  Python 3.10 or higher
  Node.js 18 or higher
  OpenAI API key
  LangSmith API key (optional but recommended)

1. Clone the repository

  git clone https://github.com/HansStewart/marketing-campaign-agent.git
  cd marketing-campaign-agent

2. Install backend dependencies

  pip install -r requirements.txt

3. Configure environment variables

  cp .env.example .env

  Open .env and fill in your values:

  OPENAI_API_KEY=your-openai-api-key-here
  LANGCHAIN_API_KEY=your-langsmith-api-key-here
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_PROJECT=marketing-campaign-agent
  OPENAI_MODEL=gpt-4o
  MODEL_TEMPERATURE=0.7

4. Start the backend

  python main.py

  Backend runs at: http://localhost:8000

5. Start the frontend

  cd frontend
  npm install
  npm run dev

  Frontend runs at: http://localhost:3000


API ENDPOINTS

GET    /health      Returns backend status and active model name
GET    /history     Returns the last 50 campaigns, most recent first
POST   /upload      Accepts .txt or .md file, extracts up to 8,000 characters
POST   /generate    Invokes the LangGraph StateGraph — runs all 4 nodes in sequence
POST   /refine      Runs a single refinement chain on a selected variant


GENERATE REQUEST BODY

  platform          string    LinkedIn, Facebook, Email, Instagram, Cold Email, etc.
  target_audience   string    Who the copy is written for
  offer             string    What is being promoted or sold
  campaign_brief    string    Full context for the campaign
  industry          string    Optional — improves tone and terminology
  persona_name      string    Optional — named persona for targeting
  persona_role      string    Optional — persona job title or role
  persona_pain      string    Optional — core pain point of the persona
  tone              string    Optional — Professional, Conversational, Bold, etc.
  output_formats    array     Optional — SHORT POST, LONG POST, STORY, EMAIL, etc.
  num_variants      integer   Optional — number of variants to generate (default 3)
  file_context      string    Optional — extracted text from an uploaded brand file


REFINE REQUEST BODY

  variant           string    The copy variant to refine
  instruction       string    Refinement instruction using labeled sections or free-form text
  platform          string    Same platform as the original request
  target_audience   string    Same audience as the original request
  offer             string    Same offer as the original request
  campaign_brief    string    Same brief as the original request
  tone              string    Optional
  industry          string    Optional
  file_context      string    Optional


COPY QUALITY RULES

Every variant produced by this agent enforces the following rules at the prompt level:

  No exclamation marks unless brand voice explicitly requires them
  No hype words: game-changer, revolutionary, unlock, skyrocket, transform, elevate
  No placeholder text such as [Your Name] or [Company]
  CTAs are always specific and action-oriented — never vague phrases like learn more
  Claims are realistic and tied to the offer, not generic marketing language
  Tone and length match the norms of the specified platform


PROJECT STRUCTURE

  main.py                    FastAPI backend — LangGraph graph, all nodes, scoring, and refine chain
  requirements.txt           Python dependencies
  .env.example               Environment variable template
  .gitignore                 Excludes .env, node_modules, pycache, and build output
  src/
    app/
      page.tsx               Main UI — campaign form, variant display, refinement panel


DEPLOYMENT

Backend — Railway
  1. Connect this repo to Railway at railway.app
  2. Set the start command to: python main.py
  3. Add all environment variables in the Railway dashboard
  4. Railway provides a public HTTPS URL for the backend

Frontend — Vercel
  1. Import this repo into Vercel at vercel.com
  2. Set root directory to: src
  3. Add environment variable: NEXT_PUBLIC_API_URL=https://your-railway-url
  4. Vercel provides a public HTTPS URL for the frontend


LICENSE

MIT License. Use freely, modify as needed.