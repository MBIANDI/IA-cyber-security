"""Normalize instrument tags so the same physical device matches across sources.

Rules (deliberately simple and inspectable):
  - upper-case, strip
  - unify spaces / underscores / dots / slashes to a single hyphen
  - insert a hyphen between the leading letter-prefix and the first digit
    (so 'FT2001' -> 'FT-2001', matching 'FT-2001' and 'FT 2001')
  - collapse repeated hyphens

This handles formatting noise. Genuine typos (e.g. letter O vs zero) survive
normalization and are caught downstream by fuzzy matching, on purpose.
"""
from __future__ import annotations

import re

_SEP = re.compile(r"[\s_./]+")


def normalize_tag(raw: str | None) -> str:
    if raw is None:
        return ""
    t = str(raw).strip().upper()
    if not t:
        return ""
    t = _SEP.sub("-", t)                      # spaces/underscores/dots/slashes -> '-'
    t = re.sub(r"^([A-Z]+)(\d)", r"\1-\2", t)  # FT2001 -> FT-2001 (prefix only)
    t = re.sub(r"-{2,}", "-", t).strip("-")    # collapse '--' and trim
    return t
