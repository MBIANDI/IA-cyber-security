"""Central configuration: paths, Claude model, matching thresholds.

Everything tunable lives here so the rest of the code stays free of magic numbers.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUTS_DIR = DATA_DIR / "outputs"

# --- Claude ------------------------------------------------------------------
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- Reconciliation thresholds (fuzzy tag matching, 0-100) -------------------
# score >= FUZZY_AUTO_ACCEPT  -> accepted automatically as a match
# FUZZY_REVIEW_FLOOR..accept  -> ambiguous, sent to the LLM / human review
# score <  FUZZY_REVIEW_FLOOR  -> treated as no match
FUZZY_AUTO_ACCEPT = 95
FUZZY_REVIEW_FLOOR = 80

# --- Calibration -------------------------------------------------------------
DUE_SOON_DAYS = 30
