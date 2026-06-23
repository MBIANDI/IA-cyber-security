"""Build and compile the LangGraph pipeline.

    ingest -> normalize -> reconcile -> (enrich if ambiguous) -> report

The conditional edge after reconcile is what makes LangGraph worthwhile here:
the LLM node only runs when there is something genuinely uncertain to resolve.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes.enrich import enrich
from .nodes.ingest import ingest
from .nodes.normalize import normalize
from .nodes.reconcile import reconcile
from .nodes.report import report
from .state import AgentState


def _route_after_reconcile(state: dict) -> str:
    return "enrich" if state.get("ambiguous") else "report"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("ingest", ingest)
    g.add_node("normalize", normalize)
    g.add_node("reconcile", reconcile)
    g.add_node("enrich", enrich)
    g.add_node("report", report)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "normalize")
    g.add_edge("normalize", "reconcile")
    g.add_conditional_edges(
        "reconcile",
        _route_after_reconcile,
        {"enrich": "enrich", "report": "report"},
    )
    g.add_edge("enrich", "report")
    g.add_edge("report", END)

    return g.compile()
