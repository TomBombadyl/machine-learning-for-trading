# Handoff — copper GNN S2 ablate (2026-09-20)

**promote=false.** Operator left while `copper_gnn_s2ablate_v0` runs on
Kaggle. Stamp from downloads only. Do not invent a verdict.

## Pickup (read in this order)

1. This file
2. `docs/synap/RECEIPT_2026-09-20_KAGGLE.md`
3. `data/synap/copper/docs/COPPER_GRAPH_HYP_CARD.md`
4. `docs/synap/GNN_RESOURCE_MAP.md`
5. `scripts/synap_copper/README.md`

## Already stamped (do not rerun)

| Version | Verdict | Note |
| ------- | ------- | ---- |
| `copper_gnn_kaggle_v0` | CONTINUE | Weak gate (hybrid vs tabular). Not S2. |
| `copper_gnn_s2gate_v0_deep` | **KILL** 0/20 | Hybrid beat MOM sum_net+DD every seed; last-5 signs **0/5 for hybrid and MOM**. Temporal failure. |

Panel sha must stay `35f1fce22bca…`. Paper MOM lock unchanged.

## What is running

- Kaggle cell: whole file `scripts/synap_copper/copper_gnn_s2ablate_kaggle.py`
- Same S2 notebook + Friday panel input
- Arms: MOM / graph_tabular / gat_emb / hybrid
- Epoch caps 50/150/250 + early-stop; seeds 42–46
- Soft gate: last-10 ≥4/10; family ≥3/5 seeds at best epoch_cap
- SHELF GAT if graph tabular alone owns the edge

## When you get back — exact next action

1. Download from `/kaggle/working/`:
   - `copper_gnn_s2ablate_memo.json`
   - `copper_gnn_s2ablate_metrics.json`
   - `copper_gnn_s2ablate_receipt.txt`
2. Confirm `sha12=35f1fce22bca` / `matches_v0`.
3. Stamp the receipt row in `docs/synap/RECEIPT_2026-09-20_KAGGLE.md` from the memo only.
4. Branch on verdict:

| Memo | Do next |
| ---- | ------- |
| `KILL` / `SHELF` | Keep `cell2_blocked`. Do not write typed GAT. Prefer graph tabular feature lane or Experiment C offline. |
| `CONTINUE` + `shelf_gat=true` | Keep graph columns; **SHELF GAT**. Still no Cell 2. |
| `CONTINUE` + `gat_adds_over_graph` | Only then open Cell 2 (typed GAT) hyp — Engine freezes card first. |

## Hard do-nots

- Rerun `copper_gnn_kaggle.py` or `copper_gnn_s2gate_kaggle.py`
- Another 20×500 epoch sweep
- `promote=true` / flip paper MOM 0.60/0.40
- Mint Cell 2 before ablate CONTINUE **and** GAT adds
- Commit research parquets / Downloads JSON

## Repo pointer

Merged on main via PR #5 (`cursor/copper-gnn-s2ablate-0ca4`).
