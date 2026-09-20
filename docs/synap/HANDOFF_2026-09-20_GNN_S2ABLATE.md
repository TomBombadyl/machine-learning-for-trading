# Handoff — copper GNN S2 ablate (2026-09-20)

**promote=false.** `copper_gnn_s2ablate_v0` finished → **KILL**.

## Stamp (from operator receipt)

```
Verdict: KILL (promote=false) version=copper_gnn_s2ablate_v0
sha12=35f1fce22bca matches_v0
audit=graph_not_redundant_vs_cot
best_epoch_cap=50; seeds_continue=0/5 floor=3
shelf_gat=False
cell2_blocked=True
```

## Family ledger (do not rerun)

| Version | Verdict | Note |
| ------- | ------- | ---- |
| `copper_gnn_kaggle_v0` | CONTINUE | Weak gate only (hybrid vs tabular). Not S2. |
| `copper_gnn_s2gate_v0_deep` | KILL 0/20 | Hybrid beat MOM sum_net+DD; last-5 = 0/5 both arms. |
| `copper_gnn_s2ablate_v0` | **KILL 0/5** | Soft last-10 gate; best cap 50; no arm CONTINUE; Cell 2 blocked. |

Panel sha `35f1fce22bca…`. Paper MOM lock unchanged.

## Exact next action

1. Optional: upload `copper_gnn_s2ablate_metrics.json` if fold_net detail is needed for a postmortem — **not required to keep Cell 2 blocked**.
2. Do **not** write typed GAT (Cell 2). Do **not** another epoch/seed sweep.
3. Offline lane: graph topology columns (`pagerank` / `betweenness` / `hhi`) stay IC survivors for tabular research on the Friday panel; attach to Experiment A / S2 v1 logistic work — not a GNN reopen.
4. Engine owns any new hyp before KaggleMLEngine runs again.

## Hard do-nots

- Rerun `copper_gnn_kaggle.py`, `copper_gnn_s2gate_kaggle.py`, `copper_gnn_s2ablate_kaggle.py`
- `promote=true` / flip paper MOM 0.60/0.40
- Mint Cell 2
- Commit research parquets / Downloads JSON
