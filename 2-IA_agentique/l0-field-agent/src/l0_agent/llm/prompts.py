"""Prompts for the single LLM task in this POC: confirming an ambiguous match.

The model is given two records and asked, JSON-only, whether they are the same
physical instrument. It never does the join itself — code already proposed the
candidate; the model only adjudicates the uncertain ones.
"""
from __future__ import annotations

import json

import pandas as pd

RESOLVE_MATCH_SYSTEM = (
    "You are an OT asset-reconciliation assistant for industrial instrument "
    "inventories. You decide whether two records — one from an instrument index, "
    "one from a CMMS — describe the SAME physical field device. Be conservative: "
    "only say they match when the tag and, where available, the manufacturer, "
    "model and description are consistent. Reply with JSON only."
)


def _g(row, key):
    try:
        if row is None or key not in row:
            return None
        v = row[key]
        if pd.isna(v):
            return None
        s = str(v).strip()
        return s or None
    except Exception:
        return None


def resolve_match_user(amb: dict, state: dict) -> str:
    inn = state.get("index_norm")
    cmn = state.get("cmms_norm")
    irow = inn.iloc[amb["index_row"]] if inn is not None else None
    crow = (
        cmn.iloc[amb["cmms_row"]]
        if (cmn is not None and amb.get("cmms_row", -1) >= 0)
        else None
    )
    payload = {
        "index_record": {
            "tag": _g(irow, "tag"),
            "description": _g(irow, "description"),
            "manufacturer": _g(irow, "manufacturer"),
            "model": _g(irow, "model"),
        },
        "cmms_record": {
            "tag": _g(crow, "tag"),
            "manufacturer": _g(crow, "manufacturer"),
            "model": _g(crow, "model"),
        },
        "fuzzy_score": amb.get("score"),
    }
    return (
        "Two records may describe the same physical instrument:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\nReply with JSON only, no prose: "
        + '{"same_asset": true/false, "confidence": 0.0-1.0, "reason": "one short sentence"}'
    )
