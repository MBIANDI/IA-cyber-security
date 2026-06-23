"""Streamlit front-end to run the L0 agent and inspect its outputs.

    streamlit run app/streamlit_app.py
"""
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from l0_agent.config import ANTHROPIC_API_KEY, SAMPLES_DIR  # noqa: E402
from l0_agent.graph import build_graph  # noqa: E402

st.set_page_config(page_title="Agent L0 — Inventaire instruments", layout="wide")
st.title("Agent L0 — Inventaire des instruments (POC)")
st.caption("Réconcilie l'index instruments et l'export CMMS. Lecture seule, hors-ligne.")

# palette (cohérente avec le design system)
GREEN, AMBER, RED, TEAL, GRAY, PURPLE = "#639922", "#EF9F27", "#E24B4A", "#1D9E75", "#888780", "#7F77DD"


def _persist(upload) -> str:
    suffix = pathlib.Path(upload.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload.getbuffer())
    tmp.close()
    return tmp.name


def to_table(assets: list[dict]) -> pd.DataFrame:
    rows = []
    for a in assets:
        rows.append({
            "asset_id": a["asset_id"],
            "tag": a["tag"],
            "description": a.get("description"),
            "in_index": a["sources"]["instrument_index"]["present"],
            "in_cmms": a["sources"]["cmms"]["present"],
            "match": a["reconciliation"]["match_method"],
            "conf": a["reconciliation"]["confidence"],
            "cal_status": a["calibration"]["status"],
            "days_overdue": a["calibration"].get("days_overdue"),
            "sil": a["sil"]["level"],
            "gaps": ", ".join(a["data_quality"]["gaps"]),
        })
    return pd.DataFrame(rows)


def style_table(df: pd.DataFrame):
    cal_colors = {
        "overdue": f"background-color:#FCEBEB;color:{RED}",
        "due_soon": f"background-color:#FAEEDA;color:#854F0B",
        "ok": f"background-color:#EAF3DE;color:#3B6D11",
        "unknown": f"color:{GRAY}",
    }
    return df.style.map(lambda v: cal_colors.get(v, ""), subset=["cal_status"])


def coverage_donut(stats: dict):
    cov = stats.get("coverage", {})
    df = pd.DataFrame({
        "Couverture": ["Dans les deux sources", "Index seul", "CMMS seul"],
        "n": [cov.get("both", 0), cov.get("index_only", 0), cov.get("cmms_only", 0)],
    })
    df = df[df["n"] > 0]
    return (
        alt.Chart(df)
        .mark_arc(innerRadius=55, stroke="white", strokeWidth=2)
        .encode(
            theta=alt.Theta("n:Q", stack=True),
            color=alt.Color(
                "Couverture:N",
                scale=alt.Scale(
                    domain=["Dans les deux sources", "Index seul", "CMMS seul"],
                    range=[TEAL, AMBER, RED],
                ),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["Couverture", "n"],
        )
        .properties(height=260)
    )


def calibration_bar(stats: dict):
    cal = stats.get("calibration", {})
    keys = ["ok", "due_soon", "overdue", "unknown"]
    labels = {"ok": "À jour", "due_soon": "Bientôt due", "overdue": "Échue", "unknown": "Inconnue"}
    order = [labels[k] for k in keys]
    colors = [GREEN, AMBER, RED, GRAY]
    df = pd.DataFrame({"Statut": order, "n": [cal.get(k, 0) for k in keys]})
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("Statut:N", sort=order, title=None),
            y=alt.Y("n:Q", title="Instruments"),
            color=alt.Color("Statut:N", scale=alt.Scale(domain=order, range=colors), legend=None),
            tooltip=["Statut", "n"],
        )
        .properties(height=260)
    )


def gap_types_bar(stats: dict):
    gt = stats.get("gap_types", {})
    if not gt:
        return None
    labels = {
        "no_cmms_record": "Sans enregistrement CMMS",
        "no_index_record": "Absent de l'index",
        "missing_sil_report_ref": "SIL sans rapport",
        "ambiguous_review": "Rapprochement à revoir",
    }
    df = pd.DataFrame({"Type d'écart": [labels.get(k, k) for k in gt], "n": list(gt.values())})
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, color=PURPLE)
        .encode(
            x=alt.X("n:Q", title="Occurrences"),
            y=alt.Y("Type d'écart:N", sort="-x", title=None),
            tooltip=["Type d'écart", "n"],
        )
        .properties(height=220)
    )


with st.sidebar:
    st.header("Sources")
    use_samples = st.toggle("Utiliser les fichiers d'exemple", value=True)
    index_path = cmms_path = None
    if use_samples:
        index_path = str(SAMPLES_DIR / "instrument_index_sample.xlsx")
        cmms_path = str(SAMPLES_DIR / "cmms_export_sample.csv")
    else:
        index_up = st.file_uploader("Index instruments (.xlsx/.csv)", type=["xlsx", "csv"])
        cmms_up = st.file_uploader("Export CMMS (.csv/.xlsx)", type=["csv", "xlsx"])
        if index_up:
            index_path = _persist(index_up)
        if cmms_up:
            cmms_path = _persist(cmms_up)

    st.divider()
    if ANTHROPIC_API_KEY:
        st.success("Claude activé — les rapprochements ambigus seront résolus par le modèle.")
    else:
        st.warning("Claude désactivé (pas de clé). Les rapprochements ambigus seront marqués à revoir manuellement.")

    run = st.button("Lancer l'inventaire", type="primary", use_container_width=True)


if run:
    if not index_path or not cmms_path:
        st.error("Il faut fournir les deux fichiers (index instruments et export CMMS).")
        st.stop()

    with st.spinner("Exécution du graphe LangGraph…"):
        graph = build_graph()
        result = graph.invoke({"index_path": index_path, "cmms_path": cmms_path})

    assets = result.get("assets", [])
    gap = result.get("gap_report", {})
    stats = gap.get("stats", {})
    score = int(stats.get("completeness_score", 0))

    # --- Synthèse ---
    if score >= 90:
        verdict, vcolor = "Inventaire cohérent", GREEN
    elif score >= 70:
        verdict, vcolor = "Quelques écarts à corriger", AMBER
    else:
        verdict, vcolor = "Inventaire incomplet — réconciliation nécessaire", RED

    st.subheader("Synthèse")
    left, right = st.columns([3, 1])
    with left:
        st.markdown(
            f"<div style='font-size:1.25rem;font-weight:600;color:{vcolor}'>{verdict}</div>",
            unsafe_allow_html=True,
        )
        st.progress(score)
        st.write(gap.get("summary", ""))
    with right:
        st.metric("Couverture croisée", f"{score}%",
                  help="Part des assets présents à la fois dans l'index et dans le CMMS.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Assets", gap.get("total_assets", 0))
    c2.metric("Index seul", len(gap.get("only_in_index", [])))
    c3.metric("CMMS seul", len(gap.get("only_in_cmms", [])))
    c4.metric("Calib. échue", len(gap.get("overdue_calibration", [])))
    c5.metric("À revoir", len(gap.get("ambiguous_unresolved", [])))

    tab_graph, tab_table, tab_json = st.tabs(["Graphiques", "Registre des assets", "Détails (JSON)"])

    with tab_graph:
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Répartition de la couverture")
            st.altair_chart(coverage_donut(stats), use_container_width=True)
        with g2:
            st.caption("Statut de calibration")
            st.altair_chart(calibration_bar(stats), use_container_width=True)
        gtchart = gap_types_bar(stats)
        if gtchart is not None:
            st.caption("Types d'écarts détectés")
            st.altair_chart(gtchart, use_container_width=True)

    with tab_table:
        st.dataframe(style_table(to_table(assets)), use_container_width=True, hide_index=True)
        if gap.get("ambiguous_unresolved"):
            st.caption("Rapprochements à revoir (le modèle ou un humain doit trancher)")
            st.dataframe(pd.DataFrame(gap["ambiguous_unresolved"]), use_container_width=True, hide_index=True)

    with tab_json:
        with st.expander("Rapport d'écarts (JSON)"):
            st.json(gap)
        with st.expander("Registre complet (JSON)"):
            st.json(assets)
        d1, d2 = st.columns(2)
        d1.download_button(
            "Télécharger le registre (JSON)",
            json.dumps(assets, ensure_ascii=False, indent=2),
            file_name="asset_register.json", mime="application/json",
            use_container_width=True,
        )
        d2.download_button(
            "Télécharger le rapport d'écarts (JSON)",
            json.dumps(gap, ensure_ascii=False, indent=2),
            file_name="gap_report.json", mime="application/json",
            use_container_width=True,
        )
else:
    st.info("Configure les sources dans la barre latérale puis clique sur **Lancer l'inventaire**.")
