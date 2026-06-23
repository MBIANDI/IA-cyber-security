"""Fuzzy tag matching via rapidfuzz. Returns (best_candidate, score 0-100)."""
from __future__ import annotations

from rapidfuzz import fuzz, process


def best_match(tag: str, candidates: list[str]) -> tuple[str | None, float]:
    if not tag or not candidates:
        return None, 0.0
    result = process.extractOne(tag, candidates, scorer=fuzz.ratio)
    if result is None:
        return None, 0.0
    candidate, score, _ = result
    return candidate, float(score)
