# Focus stall extract — 2026-09-21 (from operator log only)

**promote=false.** No `copper_s2_tabular_focus_memo.json` was uploaded.
This note salvages what the stdout log shows before the session stalled.

## Where it died

| Field | Value |
| ----- | ----- |
| Progress | topology **25 / 63**, job **~1350 / 6864** |
| Wall clock | `run_s≈15400` (~**4.3 h**) |
| Topology | `lookback=52`, `corr_min=0.25` (**primary topology**) |
| Job phase | dense primary extras (costs/thr/C/arms); had reached **h10** rows |

Checkpoint design bug (since fixed): memo was only rewritten at
**end of topology**. Mid-primary stall → disk memo likely still at
topo **24**, and in-RAM CONTINUE hits for topo 25 were lost unless
Kaggle Output still has an older memo.

**Please download from `/kaggle/working` if anything remains:**
- `copper_s2_tabular_focus_memo.json` (partial)
- any `copper_s2_tabular_focus_metrics.json`
- paste more stdout if available

## What the log still proves (topo 25 / lb52 / corr0.25)

Printed every 25 jobs. In the shared window (~job 1000–1350):

### CONTINUE 5/5 (keep)

| Snippet | Read |
| ------- | ---- |
| `h5_step26_cost12bps_…_thr0.6-0.4_C1.0_rolling_arm-shortlist_graphx…` | **5/5** |
| `h5_step26_cost16bps_…_thr0.6-0.4_C1.0_rolling_arm-shortlist_graphx…` | **5/5** |

Plain English: on the **1-week** label, with **rolling** train and the
**expanded graph+COT** arm, the stack still beat MOM at **high costs**
(12–16 bps) under the usual 0.60/0.40 thresholds and C=1.

### KILL / cont=0/5 (same window)

Most neighbors failed, including:

- higher thr bands (0.65/0.35, 0.62/0.38, …) often **0/5**
- many `expanding` + plain `shortlist` / `shortlist_graph` at 10–16 bps **0/5**
- LOO `drop-*` rows shown **0/5**
- first **h10** rows at 2 bps already **0/5** (matches prior lesson:
  longer-than-5d labels are weak)

## What we do **not** know from this log

- Whether **primary gate** passed:
  `h5 / step26 / 4bps / lb52 / corr0.25 / thr0.60-0.40 / C1 /
  expanding / shortlist_graph_cot`
  (that exact cell is not in the pasted lines)
- Results for topologies 1–24 (only “25/63” implies they finished;
  need memo for counts)
- Lookback/corr ranking tables

## Next

1. Operator: download any leftover focus memo/metrics from Kaggle Output.
2. Re-paste **updated** `copper_s2_tabular_focus_kaggle.py` (mid-job
   memo + `focus_hits.jsonl`) — or run the smaller intraday 2h/4h/12h
   cell if hourly is the priority.
3. Do not reopen GAT. Do not promote from partial logs.
