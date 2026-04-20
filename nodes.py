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
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment")
    return ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)


def strategist_node(state: CampaignState) -> Dict[str, Any]:
    llm = get_base_llm().bind(max_completion_tokens=700)
    structured_llm = llm.with_structured_output(StrategyOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior marketing strategist.

Your job is to generate concise, useful campaign planning inputs.

Hard rules:
- Return exactly 3 research insights.
- Return exactly 3 messaging angles.
- Each research insight must be under 22 words.
- Each messaging angle must be under 16 words.
- Avoid generic advice.
- Each angle must focus on a different pain point or outcome.
- Tailor ideas to the exact target audience, offer, platform, and industry.
- Use realistic business language only.
- No hype phrases."""),
        ("human", """Campaign Brief: {campaign_brief}
Target Audience: {target_audience}
Offer: {offer}
Platform: {platform}
Industry: {industry}
Tone: {tone}
Additional Context: {file_context}"""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "campaign_brief": state["campaign_brief"],
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "platform": state["platform"],
        "industry": state.get("industry") or "Not specified",
        "tone": state["tone"],
        "file_context": state.get("file_context") or "None provided",
    })

    metadata = dict(state.get("metadata", {}))
    metadata["strategist_completed"] = True

    return {
        "research_insights": result.research_insights,
        "messaging_angles": result.messaging_angles,
        "metadata": metadata,
    }


def copywriter_node(state: CampaignState) -> Dict[str, Any]:
    llm = get_base_llm().bind(max_completion_tokens=2400)
    structured_llm = llm.with_structured_output(CopyOutput)

    platforms = [p.strip() for p in state["platform"].split(",")]
    output_formats = state.get("output_formats") or []
    num_variants = state.get("num_variants") or 3

    # Build platform style block for all selected platforms
    platform_style_block = ""
    for p in platforms:
        style = PLATFORM_STYLE_MAP.get(p, "Write in a professional, concise marketing style.")
        platform_style_block += f"\n[ {p} ]\n{style}\n"

    feedback_section = ""
    if state.get("human_feedback"):
        structured_notes = []
        if state.get("human_reject_reason"):
            structured_notes.append(f"Primary rejection reason: {state['human_reject_reason']}")
        if state.get("human_reject_severity"):
            structured_notes.append(f"Rejection severity: {state['human_reject_severity']}")
        if state.get("human_tags"):
            structured_notes.append(f"Tags: {', '.join(state['human_tags'])}")
        structured_text = "\n".join(structured_notes)
        feedback_section = (
            f"\n\nHuman revision feedback:\n{structured_text}\n"
            f"Notes: {state['human_feedback']}"
        )
    elif state.get("evaluation_feedback"):
        feedback_section = f"\n\nEvaluation feedback to incorporate: {state['evaluation_feedback']}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert marketing copywriter specializing in multi-channel campaigns.

Hard rules:
- Generate {num_variants} variants for EVERY platform AND format combination specified.
- Label EACH variant clearly at the top in this exact format: [ Platform — Format ]
  Example: [ LinkedIn — Long Post ] or [ Email — Cold DM ] or [ Instagram — Story ]
- Each variant must be 45 to 110 words.
- No exclamation marks.
- No hashtags unless the platform requires them.
- No placeholders like [Your Name], [Company], or [Insert Link].
- Make each variant meaningfully different in opening and angle.
- Keep claims realistic and specific.
- End each variant with a clear, low-friction CTA.
- Adapt tone, structure, and length specifically to each platform.
- No generic hype phrases like "game-changer", "revolutionary", "unlock", "skyrocket".
- Use plain business language, not ad-speak.

Platform style instructions:
{platform_style}"""),
        ("human", """Platforms: {platform}
Output Formats: {output_formats}
Target Audience: {target_audience}
Offer: {offer}
Industry: {industry}
Tone: {tone}
Campaign Brief: {campaign_brief}
Persona Context: {persona_context}
Research Insights: {research_insights}
Messaging Angles: {messaging_angles}
Additional Context from Uploaded Files: {file_context}
{feedback_section}

Generate {num_variants} variants for each platform and format combination. Label each one clearly."""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "campaign_brief": state["campaign_brief"],
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "platform": state["platform"],
        "industry": state.get("industry") or "Not specified",
        "tone": state["tone"],
        "persona_context": state.get("persona_context") or "Not specified",
        "output_formats": ", ".join(output_formats) if output_formats else "General",
        "num_variants": num_variants,
        "research_insights": "\n".join(state.get("research_insights") or []),
        "messaging_angles": "\n".join(state.get("messaging_angles") or []),
        "feedback_section": feedback_section,
        "platform_style": platform_style_block,
        "file_context": state.get("file_context") or "None provided",
    })

    metadata = dict(state.get("metadata", {}))
    metadata["copywriter_completed"] = True

    return {
        "copy_variants": result.variants,
        "metadata": metadata,
    }


def evaluator_node(state: CampaignState) -> Dict[str, Any]:
    llm = get_base_llm().bind(max_completion_tokens=700)
    structured_llm = llm.with_structured_output(EvaluationOutput)

    variants = state.get("copy_variants") or []
    variants_text = "\n\n".join([
        f"Variant {i + 1}:\n{v}" for i, v in enumerate(variants)
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior marketing evaluator.

Evaluate each variant based on:
- hook strength
- clarity
- audience relevance
- offer presentation
- CTA quality

Hard rules:
- Return exactly one score per variant provided.
- Score each from 1.0 to 10.0.
- Return concise feedback under 60 words total.
- Approve if the best score is 7.5 or above.
- Pick the single best variant index based on overall effectiveness."""),
        ("human", """Platforms: {platform}
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
    """Auto-approve in API mode — human review only used in CLI."""
    metadata = dict(state.get("metadata", {}))
    metadata["human_review_completed"] = True
    metadata["human_decision"] = "auto-approved"

    return {
        "human_approved": True,
        "human_feedback": None,
        "human_reject_reason": None,
        "human_reject_severity": None,
        "human_tags": None,
        "metadata": metadata,
    }


def email_sequence_node(state: CampaignState) -> Dict[str, Any]:
    llm = get_base_llm().bind(max_completion_tokens=900)
    structured_llm = llm.with_structured_output(EmailSequenceOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert email copywriter.

Based on the approved campaign content, write a 3-email follow-up sequence.

Hard rules:
- Return exactly 3 emails.
- Email 1 send_day must be 1.
- Email 2 send_day must be 3.
- Email 3 send_day must be 7.
- Each email body must be 60 to 120 words.
- Each subject line must be under 7 words.
- No exclamation marks.
- No hype phrases like "game-changer", "revolutionary", "unlock", "skyrocket".
- No placeholders like [Your Name], [Company], or [Insert Link].
- No hashtags.
- One clear low-friction CTA per email.
- Plain text only.
- Avoid repeating the same closing across the 3 emails.
- Keep the sequence specific to the audience and offer."""),
        ("human", """Approved Campaign Content:
{best_variant}

Target Audience: {target_audience}
Offer: {offer}
Tone: {tone}
Additional Context: {file_context}

Generate a 3-email follow-up sequence."""),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "best_variant": state.get("best_variant", ""),
        "target_audience": state["target_audience"],
        "offer": state["offer"],
        "tone": state["tone"],
        "file_context": state.get("file_context") or "None provided",
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
    metadata = dict(state.get("metadata", {}))
    metadata["finalized"] = True
    return {"metadata": metadata}