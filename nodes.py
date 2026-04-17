"""LangChain-powered LangGraph nodes for the marketing campaign agent."""

import os
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import MODEL_NAME, MODEL_TEMPERATURE, PLATFORM_STYLE_MAP
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
    llm = get_base_llm().bind(max_completion_tokens=700)
    structured_llm = llm.with_structured_output(StrategyOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior B2B marketing strategist.

Your job is to generate concise, useful campaign planning inputs.

Hard rules:
- Return exactly 3 research insights.
- Return exactly 3 messaging angles.
- Each research insight must be under 22 words.
- Each messaging angle must be under 16 words.
- Avoid generic advice.
- Each angle must focus on a different pain point or outcome.
- Tailor the ideas to the exact target audience, offer, and platform.
- Use realistic business language only.
- No hype phrases."""),
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
    llm = get_base_llm().bind(max_completion_tokens=1200)
    structured_llm = llm.with_structured_output(CopyOutput)

    platform_style = PLATFORM_STYLE_MAP.get(
        state["platform"],
        "Write in a professional, concise marketing style.",
    )

    feedback_section = ""
    if state.get("human_feedback"):
        structured_notes = []
        if state.get("human_reject_reason"):
            structured_notes.append(
                f"Primary human rejection reason: {state['human_reject_reason']}"
            )
        if state.get("human_reject_severity"):
            structured_notes.append(
                f"Rejection severity: {state['human_reject_severity']}"
            )
        if state.get("human_tags"):
            structured_notes.append(
                f"Human tags: {', '.join(state['human_tags'])}"
            )

        structured_text = "\n".join(structured_notes)
        feedback_section = (
            f"\n\nHuman revision feedback to incorporate:\n"
            f"{structured_text}\n"
            f"Free-text notes: {state['human_feedback']}"
        )
    elif state.get("evaluation_feedback"):
        feedback_section = (
            f"\n\nEvaluation feedback to incorporate: {state['evaluation_feedback']}"
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert B2B marketing copywriter.

Hard rules:
- Return exactly 3 variants.
- Each variant must be 45 to 110 words.
- No exclamation marks.
- No hashtags unless the platform clearly requires them.
- No generic hype phrases like "game-changer", "revolutionary", "unlock", "skyrocket", "transform your business".
- No placeholders like [Your Name], [Company], or [Insert Link].
- Make each variant meaningfully different in opening and angle.
- Keep claims realistic and specific.
- End each variant with a clear, low-friction CTA.
- Adapt formatting and cadence to the target platform.
- Use plain business language, not ad-speak.
- Avoid repeating the same CTA wording across all 3 variants.

Platform style instructions:
{platform_style}"""),
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
        "research_insights": "\n".join(state.get("research_insights") or []),
        "messaging_angles": "\n".join(state.get("messaging_angles") or []),
        "feedback_section": feedback_section,
        "platform_style": platform_style,
    })

    metadata = dict(state.get("metadata", {}))
    metadata["copywriter_completed"] = True

    return {
        "copy_variants": result.variants,
        "metadata": metadata,
    }


def evaluator_node(state: CampaignState) -> Dict[str, Any]:
    """Score and select the best copy variant using LangChain + ChatOpenAI."""
    llm = get_base_llm().bind(max_completion_tokens=700)
    structured_llm = llm.with_structured_output(EvaluationOutput)

    variants = state.get("copy_variants") or []
    variants_text = "\n\n".join([
        f"Variant {i + 1}:\n{v}"
        for i, v in enumerate(variants)
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior B2B marketing evaluator.

Evaluate each variant based on:
- hook strength
- clarity
- audience relevance
- offer presentation
- CTA quality

Hard rules:
- Return exactly one score per provided variant.
- Score each variant from 1.0 to 10.0.
- Return a concise feedback summary under 60 words total.
- Approve if the best score is 8.0 or above.
- Pick the single best variant index based on overall effectiveness."""),
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

    metadata = dict(state.get("metadata", {}))
    metadata["human_review_completed"] = True

    if decision == "a":
        print("\nVariant approved by reviewer.")
        metadata["human_decision"] = "approved"
        metadata["final_label"] = "approved"

        return {
            "human_approved": True,
            "human_feedback": None,
            "human_reject_reason": None,
            "human_reject_severity": None,
            "human_tags": None,
            "metadata": metadata,
        }

    valid_reasons = {"hook", "clarity", "relevance", "offer", "cta", "other"}
    valid_severities = {"low", "med", "high"}

    reject_reason = input(
        "Main reason for rejection (hook/clarity/relevance/offer/cta/other): "
    ).strip().lower()
    while reject_reason not in valid_reasons:
        reject_reason = input(
            "Invalid choice. Enter one of: hook, clarity, relevance, offer, cta, other: "
        ).strip().lower()

    reject_severity = input("Severity (low/med/high): ").strip().lower()
    while reject_severity not in valid_severities:
        reject_severity = input(
            "Invalid choice. Enter one of: low, med, high: "
        ).strip().lower()

    raw_tags = input(
        "Optional tags (comma-separated, e.g. too-long, weak-cta, generic): "
    ).strip()
    tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()] if raw_tags else []

    feedback = input("Enter revision feedback: ").strip()

    metadata["human_decision"] = "rejected"
    metadata["final_label"] = "rejected"
    metadata["human_reject_reason"] = reject_reason
    metadata["human_reject_severity"] = reject_severity
    metadata["human_tags"] = tags

    return {
        "human_approved": False,
        "human_feedback": feedback,
        "human_reject_reason": reject_reason,
        "human_reject_severity": reject_severity,
        "human_tags": tags,
        "revision_count": state.get("revision_count", 0) + 1,
        "metadata": metadata,
    }


def email_sequence_node(state: CampaignState) -> Dict[str, Any]:
    """Generate a concise 3-email follow-up sequence from the approved best variant."""
    llm = get_base_llm().bind(max_completion_tokens=800)
    structured_llm = llm.with_structured_output(EmailSequenceOutput)

    platform_style = PLATFORM_STYLE_MAP.get(
        state["platform"],
        "Write in a professional, concise marketing style.",
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert B2B email copywriter.

Based on an approved campaign variant, write a 3-email follow-up sequence.

Hard rules:
- Return exactly 3 emails.
- Email 1 send_day must be 1.
- Email 2 send_day must be 3.
- Email 3 send_day must be 7.
- Each email body must be 60 to 120 words.
- Each subject line must be under 7 words.
- Do not use exclamation marks anywhere.
- Do not use generic hype phrases like "game-changer", "revolutionary", "unlock", "skyrocket", or "transform your business".
- Do not start more than one subject line with the same first word.
- Do not use placeholders like [Your Name], [Company], or [Insert Link].
- Do not use hashtags.
- Use exactly one clear, low-friction CTA sentence per email.
- Use plain text only.
- Avoid repeating the same closing phrasing across the 3 emails.
- Keep the sequence specific to the audience and offer.
- Keep language realistic and concrete.

Use the originating platform context to shape the voice and angle of the emails.

Platform style reference:
{platform_style}"""),
        ("human", """Approved Campaign Variant:
{best_variant}

Platform: {platform}
Target Audience: {target_audience}
Offer: {offer}
Tone: {tone}

Generate a 3-email follow-up sequence that follows all rules above."""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "best_variant": state.get("best_variant", ""),
        "platform": state["platform"],
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "tone": state["tone"],
        "platform_style": platform_style,
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
    print(f"Reject Reason:  {state.get('human_reject_reason')}")
    print(f"Severity:       {state.get('human_reject_severity')}")
    print(f"Tags:           {state.get('human_tags')}")
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