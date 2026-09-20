# Handoff — copper S2 tabular survivors (2026-09-20)

**promote=false.** `copper_s2_tabular_survivors_v0` → **CONTINUE** 5/5.
Metrics reviewed: graph/COT add costed lift; GAT stays closed.

## Headline numbers (seed-invariant on this frame)

| Arm | sum_net | maxDD | last-5 |
| --- | ------: | ----: | -----: |
| MOM | +0.102 | 0.261 | 3/5 |
| shortlist | +0.416 | **0.201** | 4/5 |
| shortlist_graph | +0.494 | 0.232 | 4/5 |
| shortlist_graph_cot | **+0.682** | 0.232 | 4/5 |

- vs shortlist: graph +0.077 sum_net / +3.1pp DD; +COT +0.265 / +3.1pp DD
- vs MOM: all three CONTINUE; best arm every seed = `shortlist_graph_cot`
- Seeds 42–46 produced identical paths (logistic + frozen features)

## Exact next action

1. Engine: freeze `shortlist_graph_cot` as the research headline stack
   on Friday panel `35f1fce22bca…` — still `promote=false`.
2. Keep shortlist as DD-cleaner ablation twin.
3. Do **not** reopen TinyGAT / Cell 2 / another GNN paste.
4. Do **not** flip paper MOM 0.60/0.40.
5. Optional leftover: S2 v1 robustness script only if Engine wants a
   second logistic re-stamp — not required for this CONTINUE.

## Hard do-nots

- Promote from this card
- Commit Downloads JSON / parquets
- Burn Tavily credits (see `API_BUDGET_TAVILY.md`)
