"""Node 5 — report: assemble the asset register and the gap report.

Deterministic. Builds one record per index instrument, adds CMMS-only orphans,
computes calibration status, and tallies the documentation gaps. The summary is
a plain templated sentence (no LLM) so the output is reproducible.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..tools.calibration import compute_calibration


def _val(row, key):
    if row is None or key not in row:
        return None
    v = row[key]
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return s or None


def report(state: dict) -> dict:
    index_norm = state.get("index_norm")
    cmms_norm = state.get("cmms_norm")
    matches = state.get("matches", [])
    ambiguous = state.get("ambiguous", [])

    now = datetime.now(timezone.utc)
    source_files = [
        Path(state.get("index_path", "")).name,
        Path(state.get("cmms_path", "")).name,
    ]

    match_by_index = {m["index_row"]: m for m in matches if m.get("index_row") is not None}
    matched_cmms_rows = {m["cmms_row"] for m in matches if m.get("cmms_row", -1) >= 0}

    assets: list[dict] = []
    only_in_index: list[str] = []
    only_in_cmms: list[str] = []
    overdue: list[str] = []
    sil_no_report: list[str] = []
    low_conf: list[str] = []
    counter = 0

    # --- index-driven assets ---
    if index_norm is not None:
        for i, row in index_norm.iterrows():
            counter += 1
            tag = _val(row, "tag") or f"UNKNOWN-{counter}"
            m = match_by_index.get(int(i))

            crow = None
            cmms_present = False
            equipment_no = None
            recon = {"match_method": "unmatched", "confidence": 0.0, "matched_to": None}

            if m:
                recon = {
                    "match_method": m["method"],
                    "confidence": m.get("confidence", 0.0),
                    "matched_to": m.get("matched_to"),
                }
                if m.get("cmms_row", -1) >= 0 and cmms_norm is not None:
                    crow = cmms_norm.iloc[m["cmms_row"]]
                    cmms_present = True
                    equipment_no = _val(crow, "equipment_no")

            cal = compute_calibration(_val(crow, "last_cal_date"), _val(crow, "frequency_months"))
            sil_raw = _val(row, "sil")
            sil_rated = bool(sil_raw) and sil_raw.upper().startswith("SIL")

            gaps = []
            if not cmms_present:
                gaps.append("no_cmms_record")
                only_in_index.append(tag)
            if sil_rated:
                gaps.append("missing_sil_report_ref")
                sil_no_report.append(tag)
            if cal["status"] == "overdue":
                overdue.append(tag)
            if recon["match_method"] in {"fuzzy", "llm_resolved"} and recon["confidence"] < 0.95:
                low_conf.append(tag)

            assets.append({
                "asset_id": f"L0-{counter:06d}",
                "tag": tag,
                "description": _val(row, "description"),
                "asset_class": _val(row, "asset_class"),
                "measurement_type": _val(row, "measurement_type"),
                "pid_ref": _val(row, "pid_ref"),
                "loop": _val(row, "loop"),
                "area_unit": _val(row, "area_unit"),
                "manufacturer": _val(row, "manufacturer") or _val(crow, "manufacturer"),
                "model": _val(row, "model") or _val(crow, "model"),
                "signal_type": _val(row, "signal_type"),
                "sil": {"rated": sil_rated, "level": sil_raw if sil_rated else None, "report_ref": None},
                "calibration": cal,
                "sources": {
                    "instrument_index": {"present": True, "row": int(i)},
                    "cmms": {"present": cmms_present, "equipment_no": equipment_no},
                },
                "reconciliation": recon,
                "data_quality": {"gaps": gaps, "flags": []},
                "provenance": {"ingested_at": now.isoformat(), "source_files": source_files},
            })

    # --- CMMS-only orphans (in maintenance system, absent from the index) ---
    if cmms_norm is not None:
        for j, row in cmms_norm.iterrows():
            if int(j) in matched_cmms_rows:
                continue
            counter += 1
            tag = _val(row, "tag") or f"CMMS-{counter}"
            only_in_cmms.append(tag)
            cal = compute_calibration(_val(row, "last_cal_date"), _val(row, "frequency_months"))
            if cal["status"] == "overdue":
                overdue.append(tag)
            assets.append({
                "asset_id": f"L0-{counter:06d}",
                "tag": tag,
                "description": None, "asset_class": None, "measurement_type": None,
                "pid_ref": None, "loop": None, "area_unit": None,
                "manufacturer": _val(row, "manufacturer"), "model": _val(row, "model"),
                "signal_type": None,
                "sil": {"rated": False, "level": None, "report_ref": None},
                "calibration": cal,
                "sources": {
                    "instrument_index": {"present": False, "row": None},
                    "cmms": {"present": True, "equipment_no": _val(row, "equipment_no")},
                },
                "reconciliation": {"match_method": "unmatched", "confidence": 0.0, "matched_to": None},
                "data_quality": {"gaps": ["no_index_record"], "flags": []},
                "provenance": {"ingested_at": now.isoformat(), "source_files": source_files},
            })

    # --- aggregates for the front-end (charts / scores) ---
    total = len(assets)
    both = sum(
        1 for a in assets
        if a["sources"]["instrument_index"]["present"] and a["sources"]["cmms"]["present"]
    )
    idx_only = sum(
        1 for a in assets
        if a["sources"]["instrument_index"]["present"] and not a["sources"]["cmms"]["present"]
    )
    cmms_only = sum(
        1 for a in assets
        if not a["sources"]["instrument_index"]["present"] and a["sources"]["cmms"]["present"]
    )

    cal_counts = {"ok": 0, "due_soon": 0, "overdue": 0, "unknown": 0}
    for a in assets:
        status = a["calibration"]["status"]
        cal_counts[status] = cal_counts.get(status, 0) + 1

    gap_counts: dict[str, int] = {}
    for a in assets:
        for g in a["data_quality"]["gaps"]:
            gap_counts[g] = gap_counts.get(g, 0) + 1
    if ambiguous:
        gap_counts["ambiguous_review"] = len(ambiguous)

    completeness = round(both / total * 100) if total else 0

    stats = {
        "coverage": {"both": both, "index_only": idx_only, "cmms_only": cmms_only},
        "calibration": cal_counts,
        "gap_types": gap_counts,
        "completeness_score": completeness,
    }

    summary = (
        f"{total} assets consolidés. "
        f"{len(only_in_index)} présents seulement dans l'index (sans enregistrement de maintenance), "
        f"{len(only_in_cmms)} seulement dans le CMMS (orphelins), "
        f"{len(set(overdue))} avec calibration échue, "
        f"{len(sil_no_report)} appareils SIL sans référence de rapport, "
        f"{len(ambiguous)} rapprochement(s) à revoir manuellement."
    )

    gap_report = {
        "total_assets": total,
        "only_in_index": only_in_index,
        "only_in_cmms": only_in_cmms,
        "overdue_calibration": sorted(set(overdue)),
        "sil_without_report": sil_no_report,
        "low_confidence_matches": low_conf,
        "ambiguous_unresolved": ambiguous,
        "stats": stats,
        "summary": summary,
    }

    return {"assets": assets, "gap_report": gap_report}
