"""Compute calibration due date and overdue status from CMMS fields.

Pure date arithmetic — no LLM. Returns ISO strings so the result is
JSON-friendly straight away.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd

from .. import config


def compute_calibration(
    last_cal: str | None,
    freq_months: str | int | None,
    today: date | None = None,
) -> dict:
    today = today or datetime.now(timezone.utc).date()
    out = {
        "last_cal_date": None,
        "frequency_months": None,
        "due_date": None,
        "status": "unknown",
        "days_overdue": None,
    }

    if last_cal:
        lc = pd.to_datetime(last_cal, errors="coerce")
        if pd.notna(lc):
            out["last_cal_date"] = lc.date().isoformat()

    if freq_months not in (None, ""):
        try:
            out["frequency_months"] = int(float(freq_months))
        except (TypeError, ValueError):
            pass

    if out["last_cal_date"] and out["frequency_months"]:
        lc = pd.to_datetime(out["last_cal_date"])
        due = (lc + pd.DateOffset(months=out["frequency_months"])).date()
        out["due_date"] = due.isoformat()
        delta = (today - due).days
        if delta > 0:
            out["status"] = "overdue"
            out["days_overdue"] = delta
        elif delta > -config.DUE_SOON_DAYS:
            out["status"] = "due_soon"
        else:
            out["status"] = "ok"

    return out
