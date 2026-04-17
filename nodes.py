from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from state import CampaignState
from schemas import StrategyOutput, CopyOutput, EvaluationOutput


base_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

strategy_llm = base_llm.with_structured_output(StrategyOutput)
copy_llm = base_llm.with_structured_output(CopyOutput)
eval_llm = base_llm.with_structured_output(EvaluationOutput)


def strategist_node(state: CampaignState) -> Dict[str, Any]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a senior growth marketing strategist.
Produce sharp, realistic strategic insights and exactly 3 differentiated messaging angles.
Do not mention that you are simulating research.
Act like an expert strategist preparing a real campaign brief.""",
            ),
            (
                "human",
                """Campaign Brief: {campaign_brief}
Target Audience: {target_audience}
Offer: {offer}
Platform: {platform}
Tone: {tone}""",
            ),
        ]
    )

    chain = prompt | strategy_llm
    result = chain.invoke(
        {
            "campaign_brief": state["campaign_brief"],
            "target_audience": state["target_audience"],
            "offer": state["offer"],
            "platform": state["platform"],
            "tone": state["tone"],
        }
    )

    return {
        "research_insights": result.research_insights,
        "messaging_angles": result.messaging_angles,
        "metadata": {
            **state.get("metadata", {}),
            "strategist_completed": True,
        },
    }


def copywriter_node(state: CampaignState) -> Dict[str, Any]:
    prior_feedback = state.get("evaluation_feedback") or ""
    revision_count = state.get("revision_count", 0)

    revision_context = ""
    if prior_feedback and revision_count > 0:
        revision_context = f"""MANDATORY REVISION INSTRUCTIONS — YOU MUST FOLLOW THESE EXACTLY:
{prior_feedback}

These instructions override your default style. Apply every instruction literally."""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a senior marketing strategist who writes campaign copy for B2B audiences.

Generate exactly 3 campaign copy variants.

Rules that cannot be broken under any circumstances:
- Zero exclamation marks anywhere in any variant
- No hook phrases like "Never Miss," "Don't let," "Say goodbye," or "Watch your"
- No promotional adjectives like cutting-edge, seamless, tirelessly, fast-paced, or transforming
- No imperative openers like "Get ready," "Start," "Elevate," or "Ready to"
- No questions used as hooks
- Every variant must open with a factual, data-driven statement
- Tone is calm, authoritative, and consultative throughout
- Maximum 100 words per variant
- Each variant must end with one calm, direct call to action — no exclamation mark

If revision feedback is provided, follow it precisely and structurally.""",
            ),
            (
                "human",
                """Campaign Brief: {campaign_brief}
Target Audience: {target_audience}
Offer: {offer}
Platform: {platform}
Tone: {tone}

Strategic Insights:
{research_insights}

Messaging Angles:
1. {angle_1}
2. {angle_2}
3. {angle_3}

{revision_context}""",
            ),
        ]
    )

    angles = state.get("messaging_angles") or ["Speed", "ROI", "24/7 Availability"]

    chain = prompt | copy_llm
    result = chain.invoke(
        {
            "campaign_brief": state["campaign_brief"],
            "target_audience": state["target_audience"],
            "offer": state["offer"],
            "platform": state["platform"],
            "tone": state["tone"],
            "research_insights": state.get("research_insights", ""),
            "angle_1": angles[0] if len(angles) > 0 else "Speed",
            "angle_2": angles[1] if len(angles) > 1 else "ROI",
            "angle_3": angles[2] if len(angles) > 2 else "24/7 Availability",
            "revision_context": revision_context,
        }
    )

    return {
        "copy_variants": result.variants,
        "revision_count": revision_count + 1,
        "metadata": {
            **state.get("metadata", {}),
            "copywriter_completed": True,
        },
    }


def evaluator_node(state: CampaignState) -> Dict[str, Any]:
    variants = state.get("copy_variants") or ["", "", ""]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a rigorous creative director and conversion strategist.
Score each variant from 0.0 to 10.0 across hook strength, clarity, audience relevance, offer strength, and CTA effectiveness.
Approve only if at least one variant scores 8.0 or higher.
Provide specific, actionable feedback if revision is needed.""",
            ),
            (
                "human",
                """Campaign Brief: {campaign_brief}
Target Audience: {target_audience}
Offer: {offer}
Platform: {platform}
Tone: {tone}

Variant 1:
{variant_1}

Variant 2:
{variant_2}

Variant 3:
{variant_3}""",
            ),
        ]
    )

    chain = prompt | eval_llm
    result = chain.invoke(
        {
            "campaign_brief": state["campaign_brief"],
            "target_audience": state["target_audience"],
            "offer": state["offer"],
            "platform": state["platform"],
            "tone": state["tone"],
            "variant_1": variants[0] if len(variants) > 0 else "",
            "variant_2": variants[1] if len(variants) > 1 else "",
            "variant_3": variants[2] if len(variants) > 2 else "",
        }
    )

    best_variant = (
        variants[result.best_variant_index]
        if variants and 0 <= result.best_variant_index < len(variants)
        else None
    )
    best_score = (
        result.scores[result.best_variant_index]
        if result.scores and 0 <= result.best_variant_index < len(result.scores)
        else None
    )

    return {
        "evaluation_scores": result.scores,
        "evaluation_feedback": result.feedback,
        "approved": result.approved,
        "best_variant": best_variant,
        "best_variant_score": best_score,
        "metadata": {
            **state.get("metadata", {}),
            "evaluator_completed": True,
        },
    }


def human_review_node(state: CampaignState) -> Dict[str, Any]:
    best_variant = state.get("best_variant") or "No variant available."
    best_score = state.get("best_variant_score")
    scores = state.get("evaluation_scores")

    print("\n" + "=" * 80)
    print("HUMAN REVIEW REQUIRED")
    print("=" * 80)
    print(f"Evaluator Scores:  {scores}")
    print(f"Best Score:        {best_score}")
    print("-" * 80)
    print("Best Variant:")
    print()
    print(best_variant)
    print("-" * 80)

    while True:
        decision = input("Decision — approve or reject? (a/r): ").strip().lower()
        if decision in {"a", "r"}:
            break
        print("Invalid input. Enter 'a' to approve or 'r' to reject.")

    if decision == "a":
        print("\nVariant approved by reviewer.")
        return {
            "human_approved": True,
            "human_feedback": None,
            "metadata": {
                **state.get("metadata", {}),
                "human_review_completed": True,
                "human_decision": "approved",
            },
        }

    feedback = input("Enter revision feedback for the copywriter: ").strip()
    print("\nVariant rejected. Routing back for revision.")

    return {
        "human_approved": False,
        "human_feedback": feedback,
        "metadata": {
            **state.get("metadata", {}),
            "human_review_completed": True,
            "human_decision": "rejected",
        },
    }


def finalize_node(state: CampaignState) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("CAMPAIGN AGENT RUN SUMMARY")
    print("=" * 80)
    print(f"Approved:       {state.get('approved')}")
    print(f"Revision Count: {state.get('revision_count')}")
    print(f"Scores:         {state.get('evaluation_scores')}")
    print(f"Best Score:     {state.get('best_variant_score')}")
    print("-" * 80)
    print("BEST VARIANT:")
    print()
    print(state.get("best_variant"))
    print("=" * 80 + "\n")

    return {
        "metadata": {
            **state.get("metadata", {}),
            "finalized": True,
        }
    }