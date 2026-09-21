# Focus stall extract — 2026-09-21 (from operator log only)

**promote=false.** No `copper_s2_tabular_focus_memo.json` was uploaded
from the stalled focus session.

## Operator re-upload 2026-09-21 (`results.zip`)

Recovered Kaggle Output pack was **not** the focus stall. It was the
already-stamped copper S2 deep_test **v0** receipt:

| File in zip | Role |
| ----------- | ---- |
| `ML4T_RECEIPT_CARD.md` / `.txt` | v0 card |
| `deep_test_s2_memo.json` | `verdict=KILL`, `passers=[]` |
| `deep_test_s2_metrics.json` | full scoreboard + COT ablation |
| `deep_test_s2_fold_table.csv` / `.json` | folds |

Matches `docs/synap/RECEIPT_2026-09-20_KAGGLE.md` § C v0 (built
`2026-09-20T05:32:12Z`, panel `35f1fce22bca…`, headline
`shortlist_log_h5` sign **2/5** → KILL). COT ablation note:
`shortlist_cot_log_h5` sign-stable 3/5 (ablation only — not a passer).

**Still missing for the focus stall:** any
`copper_s2_tabular_focus_*` memo / metrics / hits.

## Where focus_v0 died (stdout only)

| Field | Value |
| ----- | ----- |
| Progress | topology **25 / 63**, job **~1350 / 6864** |
| Wall clock | `run_s≈15400` (~**4.3 h**) |
| Topology | `lookback=52`, `corr_min=0.25` (**primary topology**) |
| Job phase | dense primary extras (costs/thr/C/arms); had reached **h10** rows |

Checkpoint design bug (**fixed in focus v1 / v1.1**): memo was only
rewritten at **end of topology**. Mid-primary stall → disk memo likely
still at topo **24**.

## What the log still proves (topo 25 / lb52 / corr0.25)

### CONTINUE 5/5 (keep)

| Snippet | Read |
| ------- | ---- |
| `h5_step26_cost12bps_…_thr0.6-0.4_C1.0_rolling_arm-shortlist_graphx…` | **5/5** |
| `h5_step26_cost16bps_…_thr0.6-0.4_C1.0_rolling_arm-shortlist_graphx…` | **5/5** |

### KILL / cont=0/5 (same window)

Most neighbors failed: extreme thr bands, many expanding plain
shortlist rows at 10–16 bps, LOO drops, early h10 at 2 bps.

## Next

1. Paste **focus v1.1** (`copper_s2_tabular_focus_v1_1`) with Persistence
   **Files only** or **Variables and Files** — see
   `docs/synap/KAGGLE_LONG_RUN.md`.
2. After PRIMARY finishes, download
   `copper_s2_tabular_focus_primary_gate.json` even if the rest is still
   running.
3. Do not reopen GAT. Do not promote from partial logs.
