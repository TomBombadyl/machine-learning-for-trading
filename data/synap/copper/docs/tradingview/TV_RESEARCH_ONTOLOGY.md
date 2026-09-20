# Copper TV research ontology

**NOT A PROMOTE.** Search-layer types for Pine Tester cards. Sits
**beside** the Engine graph hyp (`COPPER_GRAPH_HYP_CARD.md`) and
SemanticsPot. Do not join pots. Do not stamp CONTINUE/PROMOTE from
a row in `tv_cards.tsv`.

Growing table: [tv_cards.tsv](tv_cards.tsv).
Prose day card: [REPORT_2026-09-20_COPPER_TV.md](../../../../docs/synap/REPORT_2026-09-20_COPPER_TV.md).

TV = search. Engine Friday panel = held-out gate.

---

## Types

| Type | What it is | Allowed values / files |
| ---- | ---------- | ---------------------- |
| `Asset` | Chart header symbol | `FX:COPPER` (sketches so far). `COMEX:HG1!` is a different series until proven. Live intent remains CU/NCU. |
| `Strategy` | One Pine | `MOM_ONLY` → `NCU_S1_MOM_ONLY.pine`. `MOM_FRED` → `NCU_MOM_FRED.pine`. Lock twin `HG_MOM_ONLY_Weekly.pine` is not a Tester family. |
| `Side` | Book filter | `both` / `long` / `short` (`Allow longs` / `Allow shorts`) |
| `ChartTF` | Tester timeframe | chart bars, not calendar days. `1D` `2h` `4h` `5D` `7D` `12h` `21D` `1M` `63D` … |
| `Card` | One Tester run | one row in `tv_cards.tsv` |
| `Verdict` | Search label only | `sketch` `fail_bh` `snooping` `burst` `missing` `not_a_promote` |
| `Gate` | Who may promote | Operator B&H **and** Engine. TV never writes `promote=true`. |

A `Card` is not a locked candidate. `daily_63d_LME` / `weekly_MOM_COT`
are Engine IDs. Do not reuse those names on a TV row.

---

## Relations (search only)

| Edge | Meaning |
| ---- | ------- |
| `cousin_of` | `MOM_ONLY` / `MOM_FRED` → paper `paper_MOM_ONLY_weekly` (MR 0.60/0.40). z/sigmoid ≠ sklearn. |
| `same_script` | Many `ChartTF` × `Side` cards hang off one Pine. No extra files. |
| `dragged_by` | Two-sided card worse than one isolated `Side` (FRED 12h shorts dragged). |
| `overfits` | One `ChartTF` looks good; neighbors fail. |
| `burst_in` | Sub-window payday inside a weak full-window card. Not a new file. Not a conflict feature without a PIT column. |

---

## Quality process (append, don’t fork)

When a new screenshot or CSV lands:

1. Name the `Strategy`, `Asset`, `ChartTF`, `Side`, date window.
2. Write the five numbers: net %, max DD %, trades, win %, PF.
3. **Append one row** to `tv_cards.tsv`. Do not mint a new Pine.
4. Ask: same object as the paper lock? (daily Friday, calendar 5/21/63, both sides.) If no → `sketch` or `snooping`.
5. Ask: did neighbors fail? → `snooping`. Did one side carry it? → `dragged_by`.
6. Leave Engine ledger alone.

Parameters worth sweeping **inside** the two Pines (not new files):
`ChartTF`, `Side`, Friday on/off, hold 5/21/63, thresholds.

Do not sweep oil on these scripts. Oil TV has no Pine.

---

## What this is not

- Not `COPPER_GRAPH_HYP_CARD` nodes (`HG`, `COT_MM`, …).
- Not SemanticsPot families (`mega_deal`, `policy_hammer`).
- Not a paper lock rewrite.
- Not a reason to add `*_12h.pine` or `*_2h.pine`.
