"""Node 2 — normalize: map messy headers to a canonical schema and
normalize tags. This is where real-world header chaos gets tamed.
"""
from __future__ import annotations

import pandas as pd

from ..tools.tag_normalizer import normalize_tag

# canonical_name -> set of accepted (lower-cased) source headers
INDEX_HEADER_MAP = {
    "tag": {"tag", "tag no.", "tag no", "tag number", "instrument tag", "tag_no"},
    "description": {"service description", "service", "description", "desc"},
    "pid_ref": {"p&id", "pid", "p&id no", "pid ref", "drawing"},
    "loop": {"loop", "loop no", "loop number"},
    "manufacturer": {"manufacturer", "make", "vendor", "mfr"},
    "model": {"model", "model no", "type"},
    "signal_type": {"signal", "signal type", "i/o", "io type"},
    "area_unit": {"area", "unit", "area/unit", "zone"},
    "sil": {"sil", "sil rating", "sil level"},
    "measurement_type": {"measurement", "measurement type", "variable", "process variable"},
    "asset_class": {"asset class", "type of instrument", "instrument type"},
}

CMMS_HEADER_MAP = {
    "tag": {"tag", "tag no.", "functional tag", "instrument tag"},
    "equipment_no": {"equipment", "equipment no", "equipment number", "equip"},
    "func_location": {"func location", "functional location", "floc"},
    "manufacturer": {"manufacturer", "make", "vendor", "mfr"},
    "model": {"model", "model no", "type"},
    "serial_no": {"serial no", "serial number", "serial"},
    "last_cal_date": {"last calibration", "last cal", "last cal date", "calibration date"},
    "frequency_months": {
        "cal frequency (months)", "cal frequency", "calibration frequency",
        "frequency", "cal freq",
    },
}


def _rename(df: pd.DataFrame, header_map: dict) -> pd.DataFrame:
    lower = {col: str(col).strip().lower() for col in df.columns}
    rename = {}
    for canon, variants in header_map.items():
        for col, low in lower.items():
            if low in variants:
                rename[col] = canon
                break
    return df.rename(columns=rename)


def _normalize_table(df, header_map):
    if df is None:
        return None
    out = _rename(df.copy(), header_map)
    if "tag" in out.columns:
        out["tag_norm"] = out["tag"].map(normalize_tag)
    return out.reset_index(drop=True)


def normalize(state: dict) -> dict:
    return {
        "index_norm": _normalize_table(state.get("index_raw"), INDEX_HEADER_MAP),
        "cmms_norm": _normalize_table(state.get("cmms_raw"), CMMS_HEADER_MAP),
    }
