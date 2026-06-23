"""Read instrument-index / CMMS files into dataframes.

Everything is read as string to stop pandas from turning tags like '2001' into
numbers or dropping leading zeros. Cleaning happens later in normalize.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path, dtype=str)
    if suffix in {".csv", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else ","
        return pd.read_csv(path, dtype=str, sep=sep)
    raise ValueError(f"Unsupported file type: {suffix}")
