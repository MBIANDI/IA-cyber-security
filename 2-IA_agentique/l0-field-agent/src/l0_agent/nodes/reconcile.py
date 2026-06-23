"""Node 3 — reconcile: match each index tag to a CMMS record.

Exact match on normalized tags first; otherwise fuzzy. Above the auto-accept
threshold we trust it; in the grey band we hand it to the LLM/human; below, we
leave it unmatched (it becomes an index-only gap in the report).
"""
from __future__ import annotations

from .. import config
from ..tools.matcher import best_match


def reconcile(state: dict) -> dict:
    index_norm = state.get("index_norm")
    cmms_norm = state.get("cmms_norm")
    matches: list[dict] = []
    ambiguous: list[dict] = []

    if (
        index_norm is None
        or cmms_norm is None
        or "tag_norm" not in index_norm.columns
        or "tag_norm" not in cmms_norm.columns
    ):
        return {"matches": matches, "ambiguous": ambiguous}

    cmms_tags = cmms_norm["tag_norm"].tolist()
    cmms_by_tag = {t: i for i, t in enumerate(cmms_tags)}

    for i, row in index_norm.iterrows():
        tag = row.get("tag_norm", "")
        if tag and tag in cmms_by_tag:
            matches.append({
                "index_row": int(i),
                "cmms_row": int(cmms_by_tag[tag]),
                "method": "exact_tag",
                "confidence": 1.0,
                "matched_to": tag,
            })
            continue

        candidate, score = best_match(tag, cmms_tags)
        if score >= config.FUZZY_AUTO_ACCEPT:
            matches.append({
                "index_row": int(i),
                "cmms_row": int(cmms_by_tag.get(candidate, -1)),
                "method": "fuzzy",
                "confidence": round(score / 100, 3),
                "matched_to": candidate,
            })
        elif score >= config.FUZZY_REVIEW_FLOOR:
            ambiguous.append({
                "index_row": int(i),
                "index_tag": tag,
                "cmms_candidate": candidate,
                "cmms_row": int(cmms_by_tag.get(candidate, -1)),
                "score": round(score / 100, 3),
            })
        # else: no acceptable candidate -> stays index-only (handled in report)

    return {"matches": matches, "ambiguous": ambiguous}
