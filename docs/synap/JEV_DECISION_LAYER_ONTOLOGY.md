# Jev decision layer — copper ontology draft

**promote=false.** Planning only. Does **not** replace the Engine /
Kaggle WF gate. Does **not** reopen TinyGAT. Tabular focus / marathon
receipts remain the score path.

## What Jev is (cited)

From LangChain, *Building a Harness with Jev*
(https://www.langchain.com/blog/building-a-harness-with-jev) and the
hosted Decision API (https://jevtypesafeai.com/docs):

- Jev is TypeSafe AI’s **System One** model: **not** a chat LLM; it does
  not generate free text.
- Call shape: send a `state` + typed `questions` → calibrated answers.
- Three question types (parallel in one request):
  - **Choice** — pick among labelled options (+ probabilities, confidence)
  - **Score** — ordered rubric levels (+ score, distribution, confidence)
  - **Noul** — yes/no calibrated probability in `[0, 1]`
- LangChain wrapper: `langchain-typesafe` → `TypeSafeClassifier`
  (`Choice`, `Score`, `Noul`). Env: `TYPESAFE_API_KEY` (or hosted
  `JEV_API_KEY` / `jv_live_…` on jevtypesafeai.com).
- Hosted bill note (jevtypesafeai.com/docs): prepaid balance, priced per
  **input** tokens; pin a model version in production so thresholds do
  not drift.

Also: LangChain eval write-up
(https://www.langchain.com/blog/jev-agent-evals-langsmith) treats Jev as
a **decision / judge** primitive, not a generator.

## What Jev is **not** (for this repo)

| Not | Why |
| --- | --- |
| JEPA / world-model | Different acronym; do not conflate |
| Replacement for purged WF | CONTINUE/KILL stays logistic + MOM gate on Friday panel |
| TinyGAT reopen | GAT hyp closed; graph features may stay as tabular cols |
| Live order router | No promote; no broker path from Jev alone |
| Uncited UI assumption | Kaggle cell UX and Jev consoles must be verified, not guessed |

## Downstream ontology (draft types)

Keep pots separate (same rule as TV ontology vs graph hyp).

| Type | Owner path | Role |
| ---- | ---------- | ---- |
| `PanelState` | Friday panel row / fold snapshot (`35f1fce22bca…`) | Frozen numeric + text summary fed as Jev `state` |
| `WfVerdict` | Existing S2 gate | `CONTINUE` / `KILL` / `SHELF` from logistic vs MOM |
| `JevQuestion` | This doc | One Choice / Score / Noul with fixed instructions |
| `JevAnswer` | API response | Probabilities + confidence; never a promote |
| `AgreeGate` | Policy code | Threshold on Noul/Choice vs `WfVerdict` → `agree` / `veto` / `abstain` |
| `Receipt` | Kaggle / Engine ledger | Written only when WF + (optional) Jev agree policy is logged |

### Proposed first questions (not wired yet)

1. **Noul `trade_agree`** — “Given this fold/state summary, does a long
   (or short) under the locked 0.60/0.40 book agree with a cautious
   weekly copper process?” Threshold TBD; default abstain if confidence
   low.
2. **Choice `regime`** — `{trend, mean_revert, chop, abstain}` over the
   same state; diagnostic only.
3. **Score `setup_quality`** — ordered levels from “no edge / skip” to
   “clean cot+shortlist alignment”; diagnostic only.

WF `CONTINUE` without Jev remains valid research. Jev is an **optional
agree/veto layer** after the numeric gate, not a second scoreboard.

## Integration sketch (later code)

```text
Friday panel → tabular logistic WF (existing)
            → WfVerdict + fold metrics
            → build compact PanelState (text/JSON)
            → TypeSafeClassifier.invoke(state, questions)
            → AgreeGate(WfVerdict, JevAnswer) → receipt note
```

LangGraph is optional glue (node that calls Jev). Not required for v0
of the ontology. Do **not** add `langchain-typesafe` to the focus
Kaggle cell; keep that cell sklearn-only.

## Open decisions (block wiring)

1. Exact `PanelState` schema (which columns, which fold fields, max tokens).
2. Pin `jev-latest` vs a versioned `jev-x.y.z` before any threshold lock.
3. Where credentials live (operator secret only; never commit).
4. Whether AgreeGate can ever flip CONTINUE→KILL on research receipts
   (recommendation: log-only until N≥ agreed eval set).

## Exact next action

1. Finish / stamp focus v1.1 from **full** Kaggle outputs.
2. Freeze `PanelState` fields from one real CONTINUE primary cell.
3. Only then add a tiny offline `copper_jev_agree_smoke.py` (not a
   Kaggle paste) behind an explicit API key check.
