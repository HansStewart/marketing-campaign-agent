"""LangChain-powered LangGraph nodes for the marketing campaign agent.

Each node is a pure function over `CampaignState` and is orchestrated by
LangGraph in `graph.py`. Nodes use LangChain's ChatOpenAI + ChatPromptTemplate
and structured outputs defined in `schemas.py`.
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import MODEL_NAME, MODEL_TEMPERATURE
from schemas import (
    CopyOutput,
    EmailSequenceOutput,
    EvaluationOutput,
    StrategyOutput,
)
from state import CampaignState

load_dotenv()


def get_base_llm() -> ChatOpenAI:
    """Return a configured LangChain ChatOpenAI instance."""
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment")
    return ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)


def strategist_node(state: CampaignState) -> Dict[str, Any]:
    """Research insights and messaging angles using LangChain + ChatOpenAI."""
    llm = get_base_llm()
    structured_llm = llm.with_structured_output(StrategyOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior marketing strategist specializing in B2B campaigns.
Your goal is to provide actionable research insights and 3 distinct messaging angles.

Rules:
- Insights must be specific, not generic
- Each angle must be differentiated and target a different pain point
- Focus on the platform and audience provided"""),
        ("human", """Campaign Brief: {campaign_brief}
Target Audience: {target_audience}
Offer: {offer}
Platform: {platform}
Tone: {tone}"""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "campaign_brief": state["campaign_brief"],
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "platform": state["platform"],
        "tone": state["tone"],
    })

    metadata = dict(state.get("metadata", {}))
    metadata["strategist_completed"] = True

    return {
        "research_insights": result.research_insights,
        "messaging_angles": result.messaging_angles,
        "metadata": metadata,
    }


def copywriter_node(state: CampaignState) -> Dict[str, Any]:
    """Generate 3 campaign copy variants using LangChain + ChatOpenAI."""
    llm = get_base_llm()
    structured_llm = llm.with_structured_output(CopyOutput)

    feedback_section = ""
    if state.get("human_feedback"):
        feedback_section = f"\n\nRevision feedback to incorporate: {state['human_feedback']}"
    elif state.get("evaluation_feedback"):
        feedback_section = f"\n\nEvaluation feedback to incorporate: {state['evaluation_feedback']}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert marketing copywriter specializing in B2B campaigns.

Rules:
- No exclamation marks
- No generic phrases like 'game-changer', 'revolutionary', 'unlock'
- Realistic, specific, benefit-driven copy
- Each variant must use a different opening and angle
- Adapt tone and length for the specified platform
- End with a clear, low-friction CTA

Additional constraints:
- Do not include personal data beyond what is in the brief
- Do not generate discriminatory, hateful, or misleading content
- Keep all claims realistic and verifiable"""),
        ("human", """Campaign Brief: {campaign_brief}
Target Audience: {target_audience}
Offer: {offer}
Platform: {platform}
Tone: {tone}
Research Insights: {research_insights}
Messaging Angles: {messaging_angles}{feedback_section}

Write 3 distinct campaign copy variants."""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "campaign_brief": state["campaign_brief"],
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "platform": state["platform"],
        "tone": state["tone"],
        "research_insights": state.get("research_insights", ""),
        "messaging_angles": "\n".join(state.get("messaging_angles") or []),
        "feedback_section": feedback_section,
    })

    metadata = dict(state.get("metadata", {}))
    metadata["copywriter_completed"] = True

    return {
        "copy_variants": result.variants,
        "metadata": metadata,
    }


def evaluator_node(state: CampaignState) -> Dict[str, Any]:
    """Score and select the best copy variant using LangChain + ChatOpenAI."""
    llm = get_base_llm()
    structured_llm = llm.with_structured_output(EvaluationOutput)

    variants_text = "\n\n".join([
        f"Variant {i + 1}:\n{v}"
        for i, v in enumerate(state.get("copy_variants") or [])
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior marketing evaluator.
Score each variant from 1-10 across: hook strength, clarity, relevance, offer presentation, CTA quality.
Return a single average score per variant.
Approve if the best score is 8.0 or above."""),
        ("human", """Platform: {platform}
Target Audience: {target_audience}
Offer: {offer}

Variants:
{variants}

Score each variant and select the best one."""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "platform": state["platform"],
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "variants": variants_text,
    })

    variants = state.get("copy_variants") or []
    best_index = result.best_variant_index
    if best_index >= len(variants):
        best_index = 0

    metadata = dict(state.get("metadata", {}))
    metadata["evaluator_completed"] = True

    return {
        "evaluation_scores": result.scores,
        "evaluation_feedback": result.feedback,
        "approved": result.approved,
        "best_variant": variants[best_index],
        "best_variant_score": result.scores[best_index] if result.scores else None,
        "metadata": metadata,
    }


def human_review_node(state: CampaignState) -> Dict[str, Any]:
    """Pause the graph for human approval or rejection of the best variant."""
    print("\n" + "=" * 80)
    print("HUMAN REVIEW REQUIRED")
    print("=" * 80)
    print(f"Evaluator Scores:  {state.get('evaluation_scores')}")
    print(f"Best Score:        {state.get('best_variant_score')}")
    print("-" * 80)
    print("Best Variant:\n")
    print(state.get("best_variant"))
    print("-" * 80)

    decision = input("\nDecision — approve or reject? (a/r): ").strip().lower()

    if decision == "a":
        print("\nVariant approved by reviewer.")
        metadata = dict(state.get("metadata", {}))
        metadata["human_review_completed"] = True
        metadata["human_decision"] = "approved"
        return {
            "human_approved": True,
            "human_feedback": None,
            "metadata": metadata,
        }
    else:
        feedback = input("Enter revision feedback: ").strip()
        metadata = dict(state.get("metadata", {}))
        metadata["human_review_completed"] = True
        metadata["human_decision"] = "rejected"
        return {
            "human_approved": False,
            "human_feedback": feedback,
            "revision_count": state.get("revision_count", 0) + 1,
            "metadata": metadata,
        }


def email_sequence_node(state: CampaignState) -> Dict[str, Any]:
    """Generate a 3-email follow-up sequence from the approved best variant using LangChain."""
    llm = get_base_llm()
    structured_llm = llm.with_structured_output(EmailSequenceOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert B2B email copywriter.
Based on an approved campaign variant, write a 3-email follow-up sequence.

Rules:
- Email 1 (Day 1): warm intro, reference the main value proposition
- Email 2 (Day 3): provide a specific insight, stat, or story that builds credibility
- Email 3 (Day 7): low-friction final CTA, address the main objection
- No exclamation marks
- No generic phrases
- Each email must have a compelling, specific subject line
- Keep emails concise (under 150 words each)
- Maintain the tone and platform context provided"""),
        ("human", """Approved Campaign Variant:
{best_variant}

Platform: {platform}
Target Audience: {target_audience}
Offer: {offer}
Tone: {tone}

Generate a 3-email follow-up sequence."""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "best_variant": state.get("best_variant", ""),
        "platform": state["platform"],
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "tone": state["tone"],
    })

    email_list = [
        {
            "subject": email.subject,
            "body": email.body,
            "send_day": email.send_day,
        }
        for email in result.emails
    ]

    metadata = dict(state.get("metadata", {}))
    metadata["email_sequence_completed"] = True

    return {
        "email_sequence": email_list,
        "metadata": metadata,
    }


def finalize_node(state: CampaignState) -> Dict[str, Any]:
    """Print the final run summary and mark the run as finalized."""
    print("\n" + "=" * 80)
    print("CAMPAIGN AGENT RUN SUMMARY")
    print("=" * 80)
    print(f"Approved:       {state.get('human_approved')}")
    print(f"Revision Count: {state.get('revision_count')}")
    print(f"Scores:         {state.get('evaluation_scores')}")
    print(f"Best Score:     {state.get('best_variant_score')}")
    print("-" * 80)
    print("BEST VARIANT:\n")
    print(state.get("best_variant"))
    print("=" * 80)

    email_sequence = state.get("email_sequence")
    if email_sequence:
        print("\n" + "=" * 80)
        print("EMAIL FOLLOW-UP SEQUENCE")
        print("=" * 80)
        for i, email in enumerate(email_sequence, 1):
            print(f"\nEmail {i} — Send Day {email.get('send_day')}")
            print(f"Subject: {email.get('subject')}")
            print(f"Body:\n{email.get('body')}")
            print("-" * 80)

    metadata = dict(state.get("metadata", {}))
    metadata["finalized"] = True

    return {"metadata": metadata}