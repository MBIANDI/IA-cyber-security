"""Unit tests for the deterministic tools — runnable without LangGraph or Claude.

    pytest -q
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from l0_agent.tools.calibration import compute_calibration  # noqa: E402
from l0_agent.tools.matcher import best_match  # noqa: E402
from l0_agent.tools.tag_normalizer import normalize_tag  # noqa: E402


def test_tag_normalization_formats_to_same_key():
    assert normalize_tag("FT-2001") == "FT-2001"
    assert normalize_tag("FT 2001") == "FT-2001"
    assert normalize_tag("FT2001") == "FT-2001"
    assert normalize_tag("ft_2001") == "FT-2001"
    assert normalize_tag(None) == ""


def test_typo_survives_normalization():
    # letter O instead of zero must NOT be silently fixed; fuzzy catches it later
    assert normalize_tag("PT-20O6") != "PT-2006"


def test_fuzzy_match_scores_typo_high_but_not_perfect():
    cand, score = best_match("PT-20O6", ["PT-2006", "AT-2007"])
    assert cand == "PT-2006"
    assert 80 <= score < 100


def test_calibration_overdue():
    cal = compute_calibration("2024-03-15", "12", today=__import__("datetime").date(2026, 6, 23))
    assert cal["status"] == "overdue"
    assert cal["days_overdue"] > 0
    assert cal["due_date"] == "2025-03-15"


def test_calibration_ok_in_future():
    cal = compute_calibration("2026-01-15", "24", today=__import__("datetime").date(2026, 6, 23))
    assert cal["status"] == "ok"
