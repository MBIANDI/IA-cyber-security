"""The LangGraph state: what flows *through* the graph during a run.

This is volatile and internal — intermediate dataframes and match lists.
It is intentionally separate from schemas.py, which defines the stable,
public output contract (AssetRecord / GapReport).
"""
from __future__ import annotations

from typing import TypedDict

import pandas as pd


class AgentState(TypedDict, total=False):
    # --- inputs ---
    index_path: str
    cmms_path: str

    # --- intermediate (raw + normalized tables) ---
    index_raw: pd.DataFrame
    cmms_raw: pd.DataFrame
    index_norm: pd.DataFrame
    cmms_norm: pd.DataFrame

    # --- reconciliation ---
    matches: list[dict]      # resolved (exact / fuzzy / llm_resolved)
    ambiguous: list[dict]    # below auto-accept, need LLM or human review

    # --- outputs ---
    assets: list[dict]       # AssetRecord-shaped dicts
    gap_report: dict

    # --- diagnostics ---
    errors: list[str]
