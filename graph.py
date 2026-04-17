from langgraph.graph import StateGraph, END

from state import CampaignState
from nodes import (
    strategist_node,
    copywriter_node,
    evaluator_node,
    human_review_node,
    finalize_node,
)


# ─── ROUTING: AFTER EVALUATOR ─────────────────────────────────────────────────

def route_after_evaluation(state: CampaignState) -> str:
    approved = state.get("approved", False)
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 2)

    if approved:
        return "human_review"

    if revision_count >= max_revisions:
        return "human_review"

    return "revise"


# ─── ROUTING: AFTER HUMAN REVIEW ──────────────────────────────────────────────

def route_after_human_review(state: CampaignState) -> str:
    human_approved = state.get("human_approved", False)
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 2)

    if human_approved:
        return "finalize"

    if revision_count >= max_revisions:
        return "finalize"

    return "revise"


# ─── BUILD GRAPH ──────────────────────────────────────────────────────────────

def build_graph():
    workflow = StateGraph(CampaignState)

    workflow.add_node("strategist", strategist_node)
    workflow.add_node("copywriter", copywriter_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("strategist")

    workflow.add_edge("strategist", "copywriter")
    workflow.add_edge("copywriter", "evaluator")

    workflow.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "human_review": "human_review",
            "revise": "copywriter",
        },
    )

    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "finalize": "finalize",
            "revise": "copywriter",
        },
    )

    workflow.add_edge("finalize", END)

    return workflow.compile()