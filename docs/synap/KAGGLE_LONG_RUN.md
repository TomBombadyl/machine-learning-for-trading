# Kaggle long-run checklist (copper S2 tabular)

**promote=false.** Operator checklist for multi-hour paste cells.
Grounded in Kaggle’s own Persistence product note, not UI guesswork.

## What carries and what does not

From Kaggle’s Persistence announcement
([product-feedback/355440](https://www.kaggle.com/discussions/product-feedback/355440)):

| Setting | Effect |
| ------- | ------ |
| No persistence | Clean `/kaggle/working` + variables each new session |
| Files only | Files under `/kaggle/working` carry to the next interactive run |
| Variables and Files | Files + (best-effort) variables |
| Variables only | Variables only — **not** enough for our JSON dumps |

Also from that thread: persistence must be **enabled before the session
stops**; only `/kaggle/working` carries; `/kaggle/tmp` does **not**.

Community reports: variable restore is flaky; **file** restore is the
part to trust. Still download Output mid-run.

## Before you paste focus v1.1

1. Open **Notebook Options** → **Persistence** → choose **Files only**
   or **Variables and Files**.
2. Confirm Input: `synap-finpredict-panels-v0` (Friday
   `deep_test_friday_panel_v0.parquet`, sha `35f1fce22bca…`).
3. Accelerator: **None / CPU** (logistic sklearn; GPU not needed).
4. Paste **one** whole cell from
   `scripts/synap_copper/copper_s2_tabular_focus_kaggle.py`
   (`version=copper_s2_tabular_focus_v1_1`).
5. Run the cell. Expect the preflight checklist printed first.

## What the cell writes (crash-safe)

| File | When |
| ---- | ---- |
| `copper_s2_tabular_focus_heartbeat.json` | every cell (tiny progress) |
| `copper_s2_tabular_focus_primary_gate.json` | as soon as PRIMARY finishes |
| `copper_s2_tabular_focus_memo.json` | every 25 jobs + topology end |
| `copper_s2_tabular_focus_hits.jsonl` | each CONTINUE / primary row |
| `copper_s2_tabular_focus_metrics.json` | end of run |
| `copper_s2_tabular_focus_receipt.txt` | end of run |

JSON writes use temp → `os.replace` → `fsync` so a kill mid-write does
not zero the previous good file.

## If the session dies mid-run

1. Re-open the notebook (with Files persistence still on).
2. Download whatever is in Output / `/kaggle/working`:
   prefer `primary_gate` + `memo` + `hits.jsonl` + `heartbeat`.
3. Family gate is decided by **PRIMARY only**. If
   `copper_s2_tabular_focus_primary_gate.json` exists, you already have
   CONTINUE/KILL for the stamp question; later grid rows are diagnostics.
4. Do **not** reopen GAT. Do **not** promote from a partial.

## Optional durable archive

**Save Version → Save & Run All** archives notebook outputs as a
versioned kernel output. That is separate from interactive Persistence.
Use it when you want a downloadable version after a clean finish.

## Size / wallclock (v1.1)

- 12 topologies; primary first (`lb52` / `corr0.25`).
- ~438 unique cells × 5 seeds ≈ **2190** logistic pair fits.
- Primary topology alone ≈ **262** cells (the family gate).
- Prior focus_v0 stall: ~4.3 h into a much larger primary dense block.
  v1.1 is smaller, but still treat as multi-hour; leave Persistence on.
