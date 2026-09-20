# Synap copper research scripts

**NOT A PROMOTE.** Additive FinPredict / Synap Garden research helpers
beside upstream ML4T. They do not rewrite chapter notebooks, they do not
own the evidence loop, and they must never be treated as a live or paper
promotion path on their own.

## How to run

From the repository root, inside the ML4T image:

```bash
docker compose run --rm ml4t python scripts/synap_copper/<script>.py
```

Examples:

```bash
docker compose run --rm ml4t python scripts/synap_copper/multi_horizon_long_short_scorecard.py
docker compose run --rm ml4t python scripts/synap_copper/regime_backtests_locked.py
docker compose run --rm ml4t python scripts/synap_copper/paper_monitor_mom_weekly.py
```

Each script accepts `--help`. Outputs default to stdout; pass `--output`
to write a JSON report under a path you choose. Do not commit generated
reports or research parquets.

## Data

Research inputs and generated artifacts live under `data/synap/copper/`.

- **Committed:** lock JSON, docs, TradingView research ports (text only).
- **Research-machine only (never commit):** large parquets, fills, panels,
  COT/LME extracts. See `data/synap/copper/README.md`.

## Constraints

- **Free-only.** No paid API keys, no Databento/LME paid pulls from these
  scripts. CFTC COT (public) and Engine-exported free panels are the
  intended inputs.
- **Evidence loop is owned by the FinPredict Engine.** These scripts
  score, reprint locked findings, or monitor a paper lock. They do not
  mint evidence, do not change the lock, and do not promote.
- **Never promote from scripts alone.** A green local scorecard is not a
  promote. Promotion, if it ever happens, is an Engine evidence-loop
  decision recorded outside this fork.

## Scripts

| Script | Contract |
| ------ | -------- |
| `multi_horizon_long_short_scorecard.py` | Locked research candidates in `data/synap/copper/docs/MULTI_HORIZON_LONG_SHORT_SCORECARD.md` |
| `regime_backtests_locked.py` | Locked regime notes in `data/synap/copper/docs/REGIME_BACKTESTS_LOCKED.md` |
| `paper_monitor_mom_weekly.py` | Paper-only weekly MOM_ONLY lock in `data/synap/copper/docs/HG_WEEKLY_DECISION_LOCK.md` and `paper_mom_weekly_lock.json` |
| `deep_test_s2_wf_v1.py` | S2 WF v1 (turnover cost + drop zero labels). v0 = KILL. v1 = CONTINUE on `shortlist_log_h5` only (`promote=false`). Do not rerun v1. |
| `deep_test_s2_wf_robustness.py` | Paste-ready Kaggle cell. Same v1 gate, seeds 42–46. Family CONTINUE if ≥3/5 seeds pass. `promote=false`. Do not raise trees. |
| `experiment_a_cot_mom_purge.py` | Experiment A: COT+MOM IC → purge vs `fwd_ret_5d`. CONTINUE only if COT survivors. `allow_gnn=False`. |
| `copper_graph_tabular_features.py` | Ch23.4-style NetworkX columns on the Friday grid. GAT stays blocked unless graph cols survive purge. |
| `copper_gnn_hybrid.py` | TinyGAT hybrid vs tabular survivors. Trains only if graph purge survivors exist. |
| `copper_gnn_kaggle.py` | Weak-gate stamp only (hybrid vs tabular). **Do not rerun.** 14:32Z CONTINUE / `promote=false`. Gate ≠ S2. |
| `copper_gnn_s2gate_kaggle.py` | Cell 1 deep **KILL** `0/20` (sign_stable 0/5). **Do not rerun.** |
| `copper_gnn_s2ablate_kaggle.py` | S2 ablate **KILL** `0/5` (`best_epoch_cap=50`). **Do not rerun.** Cell 2 closed under this hyp. `promote=false`. |
| `copper_s2_tabular_survivors_kaggle.py` | **Stamped CONTINUE 5/5** (2026-09-20). Logistic arms: MOM / shortlist / +graph / +graph+cot. v1 WF. `promote=false`. Do not treat as paper lock. |
| `copper_s2_tabular_deep_kaggle.py` | Stress grid (horizons/step/cost) on `shortlist_graph_cot`. Primary-only family gate. No GAT. `promote=false`. |
| `copper_s2_tabular_marathon_kaggle.py` | **Stamped CONTINUE 10/10** (2026-09-20). 21 topology emits + cost/thr/C/LOO grid. Primary-only gate. No GAT. `promote=false`. Do not treat as paper lock. |

Shared candidate IDs and kill-criteria helpers live in `contract.py`.
That module is also **not a promote**.

2026-09-20: S2 WF v0 and stretch XGB are **KILL**. v1 logistic
`shortlist_log_h5` is **CONTINUE / promote=false**. See
[`docs/synap/RECEIPT_2026-09-20_KAGGLE.md`](../../docs/synap/RECEIPT_2026-09-20_KAGGLE.md)
and the next-agent prompt
[`docs/synap/RESEARCH_HANDOFF_PROMPT.md`](../../docs/synap/RESEARCH_HANDOFF_PROMPT.md).
