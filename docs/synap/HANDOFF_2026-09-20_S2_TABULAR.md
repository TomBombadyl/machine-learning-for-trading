# Handoff — copper S2 tabular survivors (2026-09-20)

**promote=false.** `copper_s2_tabular_survivors_v0` → **CONTINUE** 5/5.

## Not an error

Kaggle showed `SystemExit: 0` plus IPython “To exit: use exit…” —
that is a **successful** cell exit from `raise SystemExit(main())`,
not a failed train.

## Stamp

```
Verdict: CONTINUE (promote=false) version=copper_s2_tabular_survivors_v0
sha12=35f1fce22bca matches_v0
seeds_continue=5/5 floor=3
arm_continue_counts={'shortlist': 5, 'shortlist_graph': 5, 'shortlist_graph_cot': 5}
no_gat=True
```

## Family ledger

| Version | Verdict | Note |
| ------- | ------- | ---- |
| GNN weak / s2gate / s2ablate | CONTINUE† / KILL / KILL | †weak gate only. TinyGAT **closed** under S2. |
| `copper_s2_tabular_survivors_v0` | **CONTINUE 5/5** | Logistic shortlist ± graph ± COT. v1 gate. |

Paper MOM lock unchanged.

## Exact next action

1. Download `copper_s2_tabular_survivors_metrics.json` (optional but
   useful) — compare fold_net / sum_net / maxDD for shortlist vs
   shortlist_graph vs shortlist_graph_cot.
2. If graph/COT add lift on costed path without worse DD → keep as
   tabular feature stack for Engine; still `promote=false`.
3. If lift is flat → shortlist alone remains the CONTINUE headline.
4. Do **not** reopen GAT / Cell 2. Do **not** raise trees.

## Hard do-nots

- Treat CONTINUE as a paper or live promote
- Flip MOM thresholds
- Rerun GNN pastes
- Commit Downloads JSON / parquets
