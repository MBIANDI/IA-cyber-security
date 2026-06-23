"""Generate the sample instrument index (.xlsx) and CMMS export (.csv).

The samples are deliberately messy: mixed tag formats (FT-2001 / PT 2002 /
TT2003), one index-only instrument, one CMMS-only orphan, one typo'd tag that
only fuzzy-matches, an overdue SIL device. Run again to regenerate.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from l0_agent.config import SAMPLES_DIR  # noqa: E402

SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

index = pd.DataFrame([
    {"Tag No.": "FT-2001", "Service Description": "Reactor feed flow", "P&ID": "PID-2001", "Loop": "2001", "Manufacturer": "Emerson", "Model": "Rosemount 8800", "Signal": "4-20mA HART", "Area": "U200", "SIL": ""},
    {"Tag No.": "PT 2002", "Service Description": "Column top pressure", "P&ID": "PID-2002", "Loop": "2002", "Manufacturer": "Emerson", "Model": "Rosemount 3051S", "Signal": "4-20mA HART", "Area": "U200", "SIL": ""},
    {"Tag No.": "TT2003", "Service Description": "Feed temperature", "P&ID": "PID-2003", "Loop": "2003", "Manufacturer": "Yokogawa", "Model": "YTA610", "Signal": "4-20mA HART", "Area": "U200", "SIL": ""},
    {"Tag No.": "LT-2004", "Service Description": "Reflux drum level", "P&ID": "PID-2004", "Loop": "2004", "Manufacturer": "Endress+Hauser", "Model": "FMP51", "Signal": "4-20mA HART", "Area": "U200", "SIL": ""},
    {"Tag No.": "FT-2005", "Service Description": "ESD shutdown flow", "P&ID": "PID-2005", "Loop": "2005", "Manufacturer": "Emerson", "Model": "Micro Motion 5700", "Signal": "4-20mA HART", "Area": "U200", "SIL": "SIL2"},
    {"Tag No.": "PT-20O6", "Service Description": "Pump suction pressure", "P&ID": "PID-2006", "Loop": "2006", "Manufacturer": "Emerson", "Model": "Rosemount 3051", "Signal": "4-20mA HART", "Area": "U200", "SIL": ""},
])

cmms = pd.DataFrame([
    {"Equipment": "10004412", "Func Location": "PLANT-U200-FT2001", "Tag": "FT-2001", "Manufacturer": "Emerson", "Model": "Rosemount 8800", "Serial No": "SN-8800-01", "Last Calibration": "2025-09-01", "Cal Frequency (months)": "12"},
    {"Equipment": "10004413", "Func Location": "PLANT-U200-PT2002", "Tag": "PT-2002", "Manufacturer": "Emerson", "Model": "Rosemount 3051S", "Serial No": "SN-3051-02", "Last Calibration": "2025-11-10", "Cal Frequency (months)": "12"},
    {"Equipment": "10004414", "Func Location": "PLANT-U200-TT2003", "Tag": "TT-2003", "Manufacturer": "Yokogawa", "Model": "YTA610", "Serial No": "SN-YTA-03", "Last Calibration": "2026-01-15", "Cal Frequency (months)": "24"},
    {"Equipment": "10004415", "Func Location": "PLANT-U200-FT2005", "Tag": "FT-2005", "Manufacturer": "Emerson", "Model": "Micro Motion 5700", "Serial No": "SN-MM-05", "Last Calibration": "2024-03-15", "Cal Frequency (months)": "12"},
    {"Equipment": "10004416", "Func Location": "PLANT-U200-PT2006", "Tag": "PT-2006", "Manufacturer": "Emerson", "Model": "Rosemount 3051", "Serial No": "SN-3051-06", "Last Calibration": "2025-12-01", "Cal Frequency (months)": "12"},
    {"Equipment": "10004417", "Func Location": "PLANT-U200-AT2007", "Tag": "AT-2007", "Manufacturer": "ABB", "Model": "AZ20", "Serial No": "SN-AZ20-07", "Last Calibration": "2025-06-01", "Cal Frequency (months)": "12"},
])

index.to_excel(SAMPLES_DIR / "instrument_index_sample.xlsx", index=False)
cmms.to_csv(SAMPLES_DIR / "cmms_export_sample.csv", index=False)
print("Samples written to", SAMPLES_DIR)
