# Agent L0 — Inventaire des instruments (POC réduit)

Agent d'inventaire d'assets de **niveau 0 (instrumentation)**, version « données
structurées » : il réconcilie un **index instruments** (Excel/CSV) avec un
**export CMMS** (SAP PM), produit un registre JSON et un rapport d'écarts.
Construit avec **LangGraph** + **Claude**. Lecture seule, hors-ligne, aucun
contact avec le réseau OT.

Hors périmètre (phases suivantes) : parsing de P&ID, exports HART/Fieldbus,
données de walk-down.

## Principe clé

Le LLM **ne fait pas la jointure**. Tout ce qui est lecture de fichiers,
normalisation, rapprochement et calcul de dates est du code déterministe
(`tools/`). Claude n'intervient que dans un seul node (`nodes/enrich.py`) pour
trancher les rapprochements ambigus. **Sans clé API, le pipeline tourne quand
même** : les cas ambigus sont simplement marqués « à revoir manuellement ».

## Installation

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # puis (optionnel) renseigner ANTHROPIC_API_KEY
```

## Utilisation

```bash
python scripts/make_samples.py      # génère les fichiers d'exemple
python scripts/run_local.py         # lance le graphe en CLI -> data/outputs/*.json
streamlit run app/streamlit_app.py  # front de test : synthèse, score, graphiques, tableau
pytest -q                           # tests des briques déterministes
```

Dans le front : laisse « fichiers d'exemple » activé pour une première démo, ou
téléverse tes propres index/CMMS.

## Le pipeline

```
ingest -> normalize -> reconcile -> (enrich si ambigu) -> report
```

- **ingest** — lit les deux fichiers en dataframes (tout en texte).
- **normalize** — mappe les en-têtes désordonnés vers un schéma canonique et
  normalise les tags (`FT2001`, `FT 2001`, `FT-2001` → `FT-2001`).
- **reconcile** — rapprochement exact puis flou (rapidfuzz). Au-dessus du seuil
  d'auto-acceptation : match ; en zone grise : ambigu ; en dessous : non
  rapproché (écart index-seul).
- **enrich** — *seul node LLM*. Résout les ambigus via Claude, ou les marque à
  revoir si pas de clé.
- **report** — assemble le registre + le rapport d'écarts (déterministe).

L'arête conditionnelle après `reconcile` n'appelle `enrich` que s'il reste des
ambigus — c'est ce qui justifie LangGraph ici.

## Organisation

```
src/l0_agent/
  config.py     seuils, chemins, modèle Claude
  state.py      état LangGraph (volatil, interne)
  schemas.py    contrat de sortie pydantic (stable, public)
  graph.py      construction du StateGraph
  nodes/        une étape = un node (orchestration)
  tools/        briques déterministes pures (testables seules)
  llm/          client Claude + prompts (isolés)
app/            front Streamlit
scripts/        génération de samples + runner CLI
tests/          tests des tools
data/samples/   fichiers d'exemple
data/outputs/   JSON générés
```

## Fichiers d'exemple — ce qu'ils démontrent

| Cas | Tag | Ce que ça montre |
|-----|-----|------------------|
| Match exact | FT-2001 | rapprochement direct |
| Formats différents | PT 2002, TT2003 | la normalisation des tags |
| Index sans CMMS | LT-2004 | écart : pas d'enregistrement de maintenance |
| CMMS sans index | AT-2007 | orphelin côté maintenance |
| Faute de frappe | PT-20O6 ↔ PT-2006 | rapprochement flou → ambigu (résolu par Claude si clé) |
| SIL + calib. échue | FT-2005 | appareil SIL2 sans rapport, calibration en retard |

## Étapes suivantes possibles

- Ajouter un `SqliteSaver` + `interrupt()` pour valider les ambigus dans le front
  (human-in-the-loop) — c'est le bon prochain exercice pédagogique.
- Brancher le parsing de P&ID comme node supplémentaire sans toucher au reste.
