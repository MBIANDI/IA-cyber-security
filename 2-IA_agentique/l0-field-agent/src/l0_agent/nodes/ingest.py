"""Node 1 — ingest: read the two source files into raw dataframes."""
from __future__ import annotations

from ..tools.readers import read_table


def ingest(state: dict) -> dict:
    errors = list(state.get("errors", []))

    index_raw = None
    cmms_raw = None
    try:
        index_raw = read_table(state["index_path"])
    except Exception as e:  # noqa: BLE001
        errors.append(f"index read error: {e}")
    try:
        cmms_raw = read_table(state["cmms_path"])
    except Exception as e:  # noqa: BLE001
        errors.append(f"cmms read error: {e}")

    return {"index_raw": index_raw, "cmms_raw": cmms_raw, "errors": errors}
