"""Node 4 — enrich: the ONLY node that talks to Claude.

It adjudicates the ambiguous matches reconcile left behind. If no API key is
configured, get_llm() returns None and every ambiguous item is flagged
'needs_human_review' instead — the pipeline still completes offline.
"""
from __future__ import annotations

import json

from ..llm.client import get_llm
from ..llm.prompts import RESOLVE_MATCH_SYSTEM, resolve_match_user


def _extract_json(content) -> str:
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    content = str(content).strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lstrip().lower().startswith("json"):
            content = content.lstrip()[4:]
    return content.strip()


def enrich(state: dict) -> dict:
    ambiguous = list(state.get("ambiguous", []))
    matches = list(state.get("matches", []))
    if not ambiguous:
        return {"matches": matches, "ambiguous": ambiguous}

    llm = get_llm()
    still_ambiguous: list[dict] = []

    for amb in ambiguous:
        if llm is None:
            amb["resolution"] = "needs_human_review"
            still_ambiguous.append(amb)
            continue
        try:
            resp = llm.invoke([
                {"role": "system", "content": RESOLVE_MATCH_SYSTEM},
                {"role": "user", "content": resolve_match_user(amb, state)},
            ])
            data = json.loads(_extract_json(resp.content))
            if data.get("same_asset"):
                matches.append({
                    "index_row": amb["index_row"],
                    "cmms_row": amb["cmms_row"],
                    "method": "llm_resolved",
                    "confidence": float(data.get("confidence", amb["score"])),
                    "matched_to": amb["cmms_candidate"],
                })
            else:
                amb["resolution"] = "rejected_by_llm"
                amb["reason"] = data.get("reason", "")
                still_ambiguous.append(amb)
        except Exception as e:  # noqa: BLE001
            amb["resolution"] = f"llm_error: {e}"
            still_ambiguous.append(amb)

    return {"matches": matches, "ambiguous": still_ambiguous}
