# Synap Garden — ML4T copper operating docs

**promote=false.** Additive agent maps for copper (CU/NCU) research on
this ML4T fork. They do not rewrite chapter notebooks, do not mint
evidence, and do not promote.

Lock prose and paper JSON stay under `data/synap/copper/` (existing
scaffold). These files are the **ownership + operating map** Synap
agents should read before touching chapters or case studies.

| Doc | Use |
| --- | --- |
| [ML4T_COPPER_OWNERSHIP_MAP.md](ML4T_COPPER_OWNERSHIP_MAP.md) | Chapters / case studies / libs → bot; read vs run |
| [ML4T_EVIDENCE_LOOP_GROUNDING.md](ML4T_EVIDENCE_LOOP_GROUNDING.md) | Which repo artifacts implement each loop stage |
| [LEARNINGS_FROM_COPPER_V0.md](LEARNINGS_FROM_COPPER_V0.md) | Upgrades implied by copper v0 (SHELF counts, GraphRAG, CU gap) |
| [NEXT_ML4T_NATIVE_EXPERIMENTS.md](NEXT_ML4T_NATIVE_EXPERIMENTS.md) | Next experiments; **C GBM = KILL**; v1 `shortlist_log_h5` = CONTINUE / `promote=false` |
| [RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md) | Engine ledger: copper v0 KILL, v1 CONTINUE, stretch XGB KILL, oil CONTINUE/KILL |
| [REPORT_2026-09-20_COPPER_TV.md](REPORT_2026-09-20_COPPER_TV.md) | Copper TV initial tests (learning only; not a promote) |
| [TV ontology](../data/synap/copper/docs/tradingview/TV_RESEARCH_ONTOLOGY.md) | Search-layer types + growing `tv_cards.tsv` |
| [RESEARCH_HANDOFF_PROMPT.md](RESEARCH_HANDOFF_PROMPT.md) | Paste-ready prompt for the next agent |
| [GNN_RESOURCE_MAP.md](GNN_RESOURCE_MAP.md) | Cited papers / HF / Kaggle / official data for the copper GNN path |
| [ASSET_FM_RESOURCE_MAP.md](ASSET_FM_RESOURCE_MAP.md) | HF / official TSFMs that might be zero-shot or fine-tuned on copper or oil; sealed only |
| [HANDOFF_2026-09-20_S2_TABULAR.md](HANDOFF_2026-09-20_S2_TABULAR.md) | Tabular marathon CONTINUE 10/10; focus v1.1 long run in flight; GAT closed |
| [KAGGLE_LONG_RUN.md](KAGGLE_LONG_RUN.md) | Persistence + Output download checklist for multi-hour paste cells |
| [FOCUS_STALL_EXTRACT_2026-09-21.md](FOCUS_STALL_EXTRACT_2026-09-21.md) | focus_v0 stall salvage; `results.zip` = v0 KILL reconfirm |
| [JEV_DECISION_LAYER_ONTOLOGY.md](JEV_DECISION_LAYER_ONTOLOGY.md) | Jev/TypeSafe agree-veto layer draft; does not replace WF |

## Bot ownership (10 lines)

1. **FinPredict Engine** owns the evidence loop, ledger, promote/kill/shelf/paper, TV shortlist, and paper-monitor hygiene.
2. **CopperPotData** owns PIT copper alt features (inventory, COT, weekday/Friday panel) and free HG proxy bars.
3. **SemanticsCopperPot** owns narrative / GraphRAG (lead) and VectorRAG (ablation); raw count feats are **SHELF**.
4. **KaggleMLEngine** owns GPU/eval/sweeps only after Engine freezes a hyp; no DL until a tabular family clears IC→purge.
5. **!Flash!** owns token-efficient reads of this map + chapter READMEs; do not paste whole notebooks into context.
6. Trade targets are **Coinbase CU/NCU only**; **HG=F / CME HG** is the research proxy, not a live book.
7. Prefer **configuring** `case_studies/cme_futures` (metals includes **HG**) over a new stack.
8. Do **not** invent parallel purged CV, run logs, cost engines, or chapter rewrites.
9. Existing locks live in `data/synap/copper/docs/` — restated, not replaced.
10. **No promote without IC → purge.** `promote=false` everywhere in this tree.
