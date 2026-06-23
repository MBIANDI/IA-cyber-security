"""Run the graph from the command line on the sample files and write JSON outputs.

    python scripts/run_local.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from l0_agent.config import OUTPUTS_DIR, SAMPLES_DIR  # noqa: E402
from l0_agent.graph import build_graph  # noqa: E402


def main() -> None:
    graph = build_graph()
    state = {
        "index_path": str(SAMPLES_DIR / "instrument_index_sample.xlsx"),
        "cmms_path": str(SAMPLES_DIR / "cmms_export_sample.csv"),
    }
    result = graph.invoke(state)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "asset_register.json").write_text(
        json.dumps(result["assets"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUTS_DIR / "gap_report.json").write_text(
        json.dumps(result["gap_report"], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(result["gap_report"]["summary"])
    print(f"{len(result['assets'])} assets -> {OUTPUTS_DIR}")


if __name__ == "__main__":
    main()
