"""Claude client. Returns None when no API key is set, so the whole pipeline
still runs offline — ambiguous matches are simply flagged for human review
instead of being resolved by the model.
"""
from __future__ import annotations

from functools import lru_cache

from .. import config


@lru_cache(maxsize=1)
def get_llm():
    if not config.ANTHROPIC_API_KEY:
        return None
    # imported lazily so the dependency is only needed when a key is present
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=config.CLAUDE_MODEL,
        temperature=0,
        max_tokens=1024,
    )
