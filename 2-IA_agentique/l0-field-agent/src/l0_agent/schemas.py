"""The output contract: the stable shape every asset record must obey.

Used to validate and serialize results. If you change the JSON shape the
front-end consumes, change it here first — pydantic will catch drift.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SilInfo(BaseModel):
    rated: bool = False
    level: Optional[str] = None
    report_ref: Optional[str] = None


class CalibrationInfo(BaseModel):
    last_cal_date: Optional[date] = None
    frequency_months: Optional[int] = None
    due_date: Optional[date] = None
    status: Literal["ok", "due_soon", "overdue", "unknown"] = "unknown"
    days_overdue: Optional[int] = None


class SourcePresence(BaseModel):
    present: bool = False
    row: Optional[int] = None
    equipment_no: Optional[str] = None


class Sources(BaseModel):
    instrument_index: SourcePresence = Field(default_factory=SourcePresence)
    cmms: SourcePresence = Field(default_factory=SourcePresence)


class Reconciliation(BaseModel):
    match_method: Literal["exact_tag", "fuzzy", "llm_resolved", "unmatched"] = "unmatched"
    confidence: float = 0.0
    matched_to: Optional[str] = None


class DataQuality(BaseModel):
    gaps: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)


class Provenance(BaseModel):
    ingested_at: datetime
    source_files: list[str] = Field(default_factory=list)


class AssetRecord(BaseModel):
    asset_id: str
    tag: str
    description: Optional[str] = None
    asset_class: Optional[str] = None
    measurement_type: Optional[str] = None
    pid_ref: Optional[str] = None
    loop: Optional[str] = None
    area_unit: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    signal_type: Optional[str] = None
    sil: SilInfo = Field(default_factory=SilInfo)
    calibration: CalibrationInfo = Field(default_factory=CalibrationInfo)
    sources: Sources = Field(default_factory=Sources)
    reconciliation: Reconciliation = Field(default_factory=Reconciliation)
    data_quality: DataQuality = Field(default_factory=DataQuality)
    provenance: Provenance


class GapReport(BaseModel):
    total_assets: int
    only_in_index: list[str] = Field(default_factory=list)
    only_in_cmms: list[str] = Field(default_factory=list)
    overdue_calibration: list[str] = Field(default_factory=list)
    sil_without_report: list[str] = Field(default_factory=list)
    low_confidence_matches: list[str] = Field(default_factory=list)
    ambiguous_unresolved: list[dict] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)
    summary: str = ""
