# Agent handoff — return from focus long run (2026-09-21)

Copy everything below the line into a new agent when the operator is
back from the Kaggle focus run.

---

You are a FinPredict / KaggleMLEngine agent on
`TomBombadyl/machine-learning-for-trading`.

**promote=false.** Never write `promote=true`. Never reopen TinyGAT /
Cell 2 GNN. Never flip paper MOM 0.60/0.40. Never commit operator
Downloads / Kaggle Output JSON into git. Avoid Tavily
(`docs/synap/API_BUDGET_TAVILY.md` — Sept budget hot).

## Read first (in order)

1. `docs/synap/HANDOFF_2026-09-20_S2_TABULAR.md` — current card
2. `docs/synap/KAGGLE_LONG_RUN.md` — Persistence + which files to grab
3. `docs/synap/FOCUS_STALL_EXTRACT_2026-09-21.md` — prior stall + v0 zip note
4. `docs/synap/RECEIPT_2026-09-20_KAGGLE.md` — ledger (v0 KILL, v1 CONTINUE, marathon, survivors)
5. `docs/synap/JEV_DECISION_LAYER_ONTOLOGY.md` — parallel planning track
6. Paste script:
   `scripts/synap_copper/copper_s2_tabular_focus_kaggle.py`
   (`version=copper_s2_tabular_focus_v1_1`)

No guessing. Ground every stamp in files the operator uploads or paths
you open. If unknown: write `unknown — need <file>` and stop.

## Where we left off (2026-09-21 ~13:40Z)

- Focus **v1.1** long run was relaunched on Kaggle after Persistence
  confirmed and a ~9 min smoke check.
- Smoke showed checkpoints working and `primary_gate` **5/5 CONTINUE**
  — **smoke only, not a ledger stamp**.
- Expected wall clock ~**1–3 h** (~438 cells × 5 seeds; primary first).
- Branches:
  - `cursor/copper-s2-tabular-focus-0ca4` — paste + long-run docs (PR #14)
  - `cursor/copper-jev-ontology-0ca4` — Jev ontology draft (PR #16)
- Panel sha must stay `35f1fce22bca…` (Friday). Do not mix intraday sha.

Paste URL (if they need to re-run):
https://raw.githubusercontent.com/TomBombadyl/machine-learning-for-trading/cursor/copper-s2-tabular-focus-0ca4/scripts/synap_copper/copper_s2_tabular_focus_kaggle.py

## Exact next action (do this first)

1. Ask for / accept Kaggle Output downloads. Prefer, in order:
   - `copper_s2_tabular_focus_receipt.txt`
   - `copper_s2_tabular_focus_memo.json` (`partial: false` = finished)
   - `copper_s2_tabular_focus_metrics.json`
   - `copper_s2_tabular_focus_primary_gate.json`
   - `copper_s2_tabular_focus_hits.jsonl`
   - `copper_s2_tabular_focus_heartbeat.json` (progress if stalled)
2. Verify `version=copper_s2_tabular_focus_v1_1`,
   `panel_sha12=35f1fce22bca`, `promote=false`, `no_gat`.
3. Family stamp rule: PRIMARY cell only —
   `h5/step26/4bps/lb52/corr0.25/thr0.60-0.40/C1/expanding/shortlist_graph_cot`
   with ≥3/5 seeds CONTINUE → family CONTINUE. Else KILL.
   Diagnostics (costs, rolling, h10/h21, other lookbacks) go in notes;
   they do not flip the family gate alone.
4. Update `docs/synap/RECEIPT_2026-09-20_KAGGLE.md` (or a new dated
   receipt) + `HANDOFF_2026-09-20_S2_TABULAR.md`. Commit/push on an
   appropriate `cursor/*-0ca4` branch. Do **not** promote.
5. If still `partial: true` / no receipt: salvage like the v0 stall
   extract; do not invent a full stamp.

## Already decided (do not reopen)

| Item | Verdict |
| ---- | ------- |
| S2 deep_test v0 | **KILL** (sign 2/5); reconfirmed via operator `results.zip` |
| S2 deep_test v1 | **CONTINUE** `shortlist_log_h5` only (`promote=false`) |
| Stretch XGB / GBM | **KILL** |
| GNN / TinyGAT / s2ablate | **KILL** / closed |
| Tabular survivors | **CONTINUE 5/5** |
| Tabular marathon | **CONTINUE 10/10** |
| Paper MOM weekly lock | Unchanged |
| Jev | Ontology draft only; optional agree/veto **after** WF; not wired |

## Parallel (only after focus stamp, or if focus blocked)

- Refine `docs/synap/JEV_DECISION_LAYER_ONTOLOGY.md`: freeze `PanelState`
  fields from one real CONTINUE primary cell; no API calls unless
  operator provides a key and asks.
- Intraday 2h/4h/12h paste exists on
  `cursor/copper-s2-tabular-intraday-0ca4` — separate sha; do not mix
  with Friday panel.

## Hard do-nots

- Stamp CONTINUE from the ~9 min smoke `primary_gate` alone
- Paste GNN / GAT cells
- `promote=true`
- Commit `/kaggle/working` dumps or `uploads/` receipts as source of truth
  without summarizing into docs
- Assume Kaggle UI labels; cite `KAGGLE_LONG_RUN.md` / product notes
- Burn Tavily credits

## Done means

- Focus family CONTINUE or KILL written into a receipt doc with sha,
  version, seed counts, `elapsed_run_s`, and `partial` flag
- Handoff “exact next action” points at one concrete follow-up
- Working tree clean; branch pushed; PR updated if this agent opened one
