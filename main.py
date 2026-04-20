import logging
import uuid
import re
from datetime import datetime
from typing import Optional, List, TypedDict

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from langsmith import traceable

import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Marketing Campaign Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))

campaign_history: list = []


# ── LANGGRAPH STATE ──────────────────────────────────────────────

class CampaignState(TypedDict):
    platform: str
    target_audience: str
    offer: str
    campaign_brief: str
    industry: str
    persona_name: str
    persona_role: str
    persona_pain: str
    tone: str
    output_formats: list
    num_variants: int
    file_context: str
    raw_output: str
    all_variants: list
    variant_scores: list
    best_variant: str
    best_variant_score: float
    email_sequence: list


# ── REQUEST MODELS ──────────────────────────────────────────────

class CampaignRequest(BaseModel):
    platform: str
    target_audience: str
    offer: str
    campaign_brief: str
    industry: Optional[str] = ""
    persona_name: Optional[str] = ""
    persona_role: Optional[str] = ""
    persona_pain: Optional[str] = ""
    tone: Optional[str] = ""
    output_formats: Optional[List[str]] = []
    num_variants: Optional[int] = 3
    file_context: Optional[str] = ""


class RefineRequest(BaseModel):
    variant: str
    instruction: str
    platform: str
    target_audience: str
    offer: str
    campaign_brief: str
    tone: Optional[str] = ""
    industry: Optional[str] = ""
    file_context: Optional[str] = ""


# ── HELPERS ─────────────────────────────────────────────────────

def build_persona_block(name: str, role: str, pain: str) -> str:
    parts = []
    if name:
        parts.append(f"Name: {name}")
    if role:
        parts.append(f"Role: {role}")
    if pain:
        parts.append(f"Core pain point: {pain}")
    if parts:
        return "Target Persona:\n" + "\n".join(parts)
    return ""


def score_variant(variant: str, brief: str, audience: str, llm: ChatOpenAI) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a direct-response marketing evaluator.
Score the following marketing copy on a scale of 0.0 to 1.0 based on:
- Hook strength (does it grab attention immediately?)
- Clarity (is the offer and audience clear?)
- CTA effectiveness (is the call-to-action specific and compelling?)
- Tone match (does it suit the brief and audience?)
- Absence of hype (no empty buzzwords, no exclamation overuse)

Return your response in this exact format:
SCORE: [0.0-1.0]
REASONING: [one sentence]"""),
        ("human", "Copy:\n{variant}\n\nBrief:\n{brief}\n\nAudience:\n{audience}"),
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({"variant": variant, "brief": brief, "audience": audience})
        score = 0.7
        reasoning = ""
        for line in result.strip().split("\n"):
            if line.startswith("SCORE:"):
                try:
                    score = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    pass
            if line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
        return {"variant": variant, "score": score, "reasoning": reasoning}
    except Exception as e:
        logger.warning("Scoring failed: %s", e)
        return {"variant": variant, "score": 0.7, "reasoning": ""}


def parse_email_sequence(raw: str) -> List[dict]:
    emails = []
    blocks = re.split(r"EMAIL\s+\d+", raw, flags=re.IGNORECASE)
    for block in blocks:
        if not block.strip():
            continue
        send_day = 1
        subject = ""
        body = ""
        day_match = re.search(r"SEND_DAY:\s*(\d+)", block, re.IGNORECASE)
        if day_match:
            send_day = int(day_match.group(1))
        subj_match = re.search(r"SUBJECT:\s*(.+)", block, re.IGNORECASE)
        if subj_match:
            subject = subj_match.group(1).strip()
        body_match = re.search(r"BODY:\s*\n([\s\S]+)", block, re.IGNORECASE)
        if body_match:
            body = body_match.group(1).strip()
        if subject or body:
            emails.append({"subject": subject, "body": body, "send_day": send_day})
    return emails[:3]


# ── LANGGRAPH NODES ──────────────────────────────────────────────

@traceable(name="copywrite_node")
def copywrite_node(state: CampaignState) -> CampaignState:
    llm = ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)
    persona_block = build_persona_block(
        state.get("persona_name", ""),
        state.get("persona_role", ""),
        state.get("persona_pain", ""),
    )
    formats_block = (
        "Output formats requested: " + ", ".join(state.get("output_formats", []))
        if state.get("output_formats") else ""
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite direct-response marketing copywriter.

Your job is to write high-converting marketing copy for the specified platform and audience.

Rules:
- Write copy that sounds human, specific, and credible.
- Match the tone and length norms of the platform exactly.
- Lead with the strongest hook — pain point, bold claim, or pattern interrupt.
- End with a clear, specific CTA. Never vague ("learn more"). Always action-specific ("Reply YES", "Book a 15-min call", "DM me the word READY").
- No exclamation marks unless the brand voice explicitly calls for them.
- No hype: "game-changer", "revolutionary", "unlock", "skyrocket", "transform", "elevate".
- No placeholders like [Your Name] or [Company].
- Keep claims realistic and specific.
- If output formats are specified, label each section clearly (e.g. "--- SHORT POST ---").
- If multiple variants are requested, separate each with "--- VARIANT [N] ---" on its own line."""),
        ("human", """Platform: {platform}
Industry: {industry}
Target Audience: {target_audience}
Offer / Product: {offer}
Campaign Brief: {campaign_brief}
Tone: {tone}
{persona_block}
{formats_block}
File / Brand Context: {file_context}
Number of variants to write: {num_variants}

Write {num_variants} distinct variant(s) of marketing copy for this campaign."""),
    ])
    chain = prompt | llm | StrOutputParser()
    raw_output = chain.invoke({
        "platform": state["platform"],
        "industry": state.get("industry") or "Not specified",
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "campaign_brief": state["campaign_brief"],
        "tone": state.get("tone") or "Professional",
        "persona_block": persona_block,
        "formats_block": formats_block,
        "file_context": state.get("file_context") or "None provided",
        "num_variants": state.get("num_variants", 3),
    })
    return {**state, "raw_output": raw_output}


@traceable(name="parse_node")
def parse_node(state: CampaignState) -> CampaignState:
    raw = state.get("raw_output", "")
    if "--- VARIANT" in raw:
        parts = re.split(r"---\s*VARIANT\s*\d+\s*---", raw, flags=re.IGNORECASE)
        variants = [p.strip() for p in parts if p.strip()]
    else:
        variants = [raw.strip()]
    return {**state, "all_variants": variants}


@traceable(name="score_node")
def score_node(state: CampaignState) -> CampaignState:
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.2)
    scores = []
    for v in state.get("all_variants", []):
        result = score_variant(v, state["campaign_brief"], state["target_audience"], llm)
        scores.append(result)
    best = max(scores, key=lambda x: x["score"]) if scores else {}
    return {
        **state,
        "variant_scores": scores,
        "best_variant": best.get("variant", ""),
        "best_variant_score": best.get("score", 0.0),
    }


@traceable(name="email_node")
def email_node(state: CampaignState) -> CampaignState:
    platform = state.get("platform", "").lower()
    formats = state.get("output_formats", [])
    if "email" not in platform and "email" not in [f.lower() for f in formats]:
        return {**state, "email_sequence": []}
    llm = ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an email marketing specialist.
Write a 3-email nurture sequence based on the campaign brief.
Return exactly 3 emails. For each email use this format:

EMAIL 1
SEND_DAY: [number]
SUBJECT: [subject line]
BODY:
[email body]

EMAIL 2
SEND_DAY: [number]
SUBJECT: [subject line]
BODY:
[email body]

EMAIL 3
SEND_DAY: [number]
SUBJECT: [subject line]
BODY:
[email body]

Rules:
- Email 1: Awareness / hook
- Email 2: Value / proof
- Email 3: CTA / urgency
- No exclamation marks. No hype words. Specific, human copy."""),
        ("human", """Audience: {target_audience}
Offer: {offer}
Brief: {campaign_brief}
Tone: {tone}

Write the 3-email sequence."""),
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        raw = chain.invoke({
            "target_audience": state["target_audience"],
            "offer": state["offer"],
            "campaign_brief": state["campaign_brief"],
            "tone": state.get("tone") or "Professional",
        })
        return {**state, "email_sequence": parse_email_sequence(raw)}
    except Exception as e:
        logger.warning("Email sequence generation failed: %s", e)
        return {**state, "email_sequence": []}


# ── LANGGRAPH GRAPH ──────────────────────────────────────────────

def build_campaign_graph():
    graph = StateGraph(CampaignState)
    graph.add_node("copywrite", copywrite_node)
    graph.add_node("parse", parse_node)
    graph.add_node("score", score_node)
    graph.add_node("email", email_node)
    graph.add_edge(START, "copywrite")
    graph.add_edge("copywrite", "parse")
    graph.add_edge("parse", "score")
    graph.add_edge("score", "email")
    graph.add_edge("email", END)
    return graph.compile()

campaign_graph = build_campaign_graph()


# ── ROUTES ──────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.get("/history")
def get_history():
    return {"history": list(reversed(campaign_history[-50:]))}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info("File uploaded: %s", file.filename)
    text_content = ""
    try:
        if file.filename and (
            file.filename.endswith(".txt") or file.filename.endswith(".md")
        ):
            raw = await file.read()
            text_content = raw.decode("utf-8", errors="ignore")[:8000]
        else:
            await file.read()
    except Exception as e:
        logger.warning("File read error: %s", e)
    return {
        "filename": file.filename,
        "text_content": text_content,
        "status": "uploaded",
    }


@app.post("/generate")
@traceable(name="generate_endpoint")
def generate(req: CampaignRequest):
    logger.info("Generate — platform: %s, variants: %s", req.platform, req.num_variants)

    initial_state: CampaignState = {
        "platform": req.platform,
        "target_audience": req.target_audience,
        "offer": req.offer,
        "campaign_brief": req.campaign_brief,
        "industry": req.industry or "",
        "persona_name": req.persona_name or "",
        "persona_role": req.persona_role or "",
        "persona_pain": req.persona_pain or "",
        "tone": req.tone or "Professional",
        "output_formats": req.output_formats or [],
        "num_variants": req.num_variants or 3,
        "file_context": req.file_context or "",
        "raw_output": "",
        "all_variants": [],
        "variant_scores": [],
        "best_variant": "",
        "best_variant_score": 0.0,
        "email_sequence": [],
    }

    result = campaign_graph.invoke(initial_state)

    campaign_history.append({
        "id": str(uuid.uuid4()),
        "ts": datetime.now().strftime("%b %d, %Y %I:%M %p"),
        "platform": req.platform,
    })

    return {
        "best_variant": result["best_variant"],
        "best_variant_score": result["best_variant_score"],
        "all_variants": result["all_variants"],
        "variant_scores": result["variant_scores"],
        "evaluation_scores": [s["score"] for s in result["variant_scores"]],
        "email_sequence": result["email_sequence"],
    }


@app.post("/refine")
@traceable(name="refine_endpoint")
def refine(req: RefineRequest):
    logger.info("Refine request — platform: %s", req.platform)

    llm = ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior marketing copywriter and editor.

You are given an existing piece of marketing copy and a detailed refinement instruction from the user.

Your job is to rewrite ONLY that copy, applying every part of the instruction precisely.

The instruction may contain labeled sections like:
- Change: [what to rewrite]
- Keep: [what to preserve]
- Tone: [tone direction]
- Length: [word/sentence targets]
- CTA: [specific call-to-action rewrite]
- Note: [additional constraints]

Apply all of these exactly as specified. If there are no labeled sections, interpret the instruction as free-form guidance and apply it thoughtfully.

Hard rules:
- Return only the rewritten copy — no preamble, no explanation, no label headers.
- No placeholders like [Your Name] or [Company].
- No exclamation marks unless the original contained them and the instruction says to keep them.
- No hype phrases: "game-changer", "revolutionary", "unlock", "skyrocket", "transform" (unless the instruction explicitly allows them).
- Maintain realistic, specific claims.
- If a length target is given, hit it as closely as possible.
- If "Keep:" is specified, preserve those elements verbatim or near-verbatim."""),
        ("human", """=== ORIGINAL COPY ===
{variant}

=== REFINEMENT INSTRUCTION ===
{instruction}

=== CAMPAIGN CONTEXT ===
Platform: {platform}
Target Audience: {target_audience}
Offer: {offer}
Campaign Brief: {campaign_brief}
Tone: {tone}
Industry: {industry}
File Context: {file_context}

Rewrite the copy applying every part of the refinement instruction above."""),
    ])

    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({
        "variant": req.variant,
        "instruction": req.instruction,
        "platform": req.platform,
        "target_audience": req.target_audience,
        "offer": req.offer,
        "campaign_brief": req.campaign_brief,
        "tone": req.tone or "Professional",
        "industry": req.industry or "Not specified",
        "file_context": req.file_context or "None provided",
    })

    return {"refined_variant": result}


# ── ENTRY POINT ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)