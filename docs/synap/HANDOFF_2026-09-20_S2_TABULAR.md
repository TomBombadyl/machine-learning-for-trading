# Handoff — copper S2 tabular (2026-09-21)

**promote=false.** Marathon CONTINUE 10/10 and survivors CONTINUE 5/5
still stand. GAT stays closed. Focus **long run launched** after a short
smoke check — **do not stamp CONTINUE from the smoke dump**.

## Marathon stamp (unchanged)

| Field | Value |
| ----- | ----- |
| Panel | `35f1fce22bca…` `matches_v0` |
| Primary | h5 / step26 / 4bps / lb52 / corr0.25 / thr0.60–0.40 / C=1.0 / full |
| Seeds continue | **10/10** (floor 6) |
| Wall clock | `elapsed_run_s=3701` (~1.0 h) |
| `no_gat` | True |

## Focus v1.1 status (2026-09-21)

| Item | Status |
| ---- | ------ |
| Paste | `copper_s2_tabular_focus_v1_1` on branch `cursor/copper-s2-tabular-focus-0ca4` |
| Persistence | Operator confirmed Files / Variables+Files |
| Smoke (~9 min) | Checkpoints worked; PRIMARY file showed 5/5 — **smoke only** |
| Long run | Operator re-pasted and left running (~1–3 h expected) |
| Stamp | **Wait** for end-of-run `memo` + `metrics` + `receipt` |

Paste URL:
https://raw.githubusercontent.com/TomBombadyl/machine-learning-for-trading/cursor/copper-s2-tabular-focus-0ca4/scripts/synap_copper/copper_s2_tabular_focus_kaggle.py

## Exact next action

1. When the long run finishes (or stalls): download from Output —
   `primary_gate`, `memo`, `metrics`, `receipt`, `hits.jsonl`,
   `heartbeat`. Stamp only from a finished (or clearly primary-complete)
   pack; never from the ~9 min smoke alone.
2. Parallel track: Jev / TypeSafe decision-layer ontology — see
   `docs/synap/JEV_DECISION_LAYER_ONTOLOGY.md` on branch
   `cursor/copper-jev-ontology-0ca4`. Does **not** replace the WF gate.
3. Do **not** paste another GNN / TinyGAT / Cell 2 cell.
4. Do **not** flip paper MOM 0.60/0.40.
5. Do **not** mix intraday sha with Friday `35f1fce22bca…`.

## Hard do-nots

- Promote from this card
- Commit Downloads JSON / parquets / operator uploads
- Burn Tavily credits (see `API_BUDGET_TAVILY.md`)
- Treat smoke primary_gate as a ledger CONTINUE
