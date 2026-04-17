"""LangGraph state machine wiring for the marketing campaign agent.

Defines the LangGraph `StateGraph` that routes state through:
strategist -> copywriter -> evaluator -> human_review -> email_sequence -> finalize.

`build_graph()` compiles the graph into an app invoked by `main.py`.
"""

from langgraph.graph import END, START, StateGraph

from nodes import (
    copywriter_node,
    email_sequence_node,
    evaluator_node,
    finalize_node,
    human_review_node,
    strategist_node,
)
from state import CampaignState


def route_after_evaluation(state: CampaignState) -> str:
    """Route to human_review if approved, back to copywriter if not and revisions remain."""
    if state.get("approved"):
        return "human_review"
    if state.get("revision_count", 0) >= state.get("max_revisions", 4):
        return "human_review"
    return "copywriter"


def route_after_human_review(state: CampaignState) -> str:
    """Route to email_sequence if approved, back to copywriter if rejected."""
    if state.get("human_approved"):
        return "email_sequence"
    if state.get("revision_count", 0) >= state.get("max_revisions", 4):
        return "email_sequence"
    return "copywriter"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph campaign agent workflow."""
    graph = StateGraph(CampaignState)

    graph.add_node("strategist", strategist_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("email_sequence", email_sequence_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "strategist")
    graph.add_edge("strategist", "copywriter")
    graph.add_edge("copywriter", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "human_review": "human_review",
            "copywriter": "copywriter",
        },
    )

    graph.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "email_sequence": "email_sequence",
            "copywriter": "copywriter",
        },
    )

    graph.add_edge("email_sequence", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()