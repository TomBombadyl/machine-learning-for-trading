# Asset fine-tune / forecast model map

**promote=false.** Cited inventory of Hugging Face and official
open-source time-series / finance models that *might* be zero-shot or
fine-tuned on a named copper or oil series. Not a train card. Not a
paper lock. Do not mix any of these datasets into
`deep_test_friday_panel_v0` (sha `35f1fce22bca…`).

Grounding: this repo, Hugging Face **MCP**
(`hub_repo_search` / `hub_repo_details` as `TomBombadyl`, org
[SynapGarden](https://huggingface.co/SynapGarden) admin, 2026-09-20),
Hugging Face model cards fetched the same day, or Tavily research run
`55711173-9e6e-453a-9c30-93acfd22b4cc`. If a row is not in those, it
is marked unknown. SynapGarden has **zero** Hub models/datasets.
**Sept 2026:** do not re-run that Tavily inventory — see
[API_BUDGET_TAVILY.md](API_BUDGET_TAVILY.md) (~80% month quota used).

Local ledger: [RECEIPT_2026-09-20_KAGGLE.md](RECEIPT_2026-09-20_KAGGLE.md).
GNN path: [GNN_RESOURCE_MAP.md](GNN_RESOURCE_MAP.md).
ML4T home for foundation models: [13_dl_time_series/README.md](../../13_dl_time_series/README.md)
`09_foundation_models` (Chronos + TinyTimeMixer; names **pretraining
contamination**).

---

## What this repo already decided

- Copper GAT Cell 1 is [scripts/synap_copper/copper_gnn_s2gate_kaggle.py](../../scripts/synap_copper/copper_gnn_s2gate_kaggle.py)
  (from-scratch TinyGAT vs MOM). Do not replace it with a HF TSFM.
- Oil TCN/TCNN family is **KILL**. Brent EIA logistic is CONTINUE
  research-only. No oil paper lock.
- Ch13: sequence models must beat a linear / ridge baseline. Foundation
  models are a **sealed** zero-shot (or later fine-tune) on the **same**
  purged Friday frame.

---

## Hugging Face MCP search (2026-09-20)

Live Hub, not a scraped Models index. Empty = the API returned
**no repositories**.

| MCP call | Result |
| -------- | ------ |
| `hub_repo_search` `copper futures forecast` (models+datasets, sort downloads) | **No repositories** |
| `hub_repo_search` `oil WTI Brent crude forecast` | **No repositories** |
| `hub_repo_search` `WTI oil price` | **No repositories** |
| `hub_repo_search` `oil crude WTI` (models) | **No repositories** |
| `hub_repo_search` `finance commodity oil copper` + filter `time-series-forecasting` | **No repositories** |
| `author=SynapGarden` | **No repositories** |
| `hub_repo_search` `copper` (top downloads) | Name collisions only (LLMs / image LoRAs / robotics “copper screw”). **No** HG/CME TSFM. |
| `hub_repo_search` `CrudeBERT` | [Captain-1337/CrudeBERT](https://hf.co/Captain-1337/CrudeBERT) — `text-classification`, BERT |
| `hub_repo_search` `EXAONE Forecast Finance` | [LG-AI-Research/EXAONE-Forecast-for-Finance-1.0](https://hf.co/LG-AI-Research/EXAONE-Forecast-for-Finance-1.0) |
| filter `time-series-forecasting` sort downloads | Chronos-2 / Chronos-Bolt, TimesFM, **Kronos** (candlestick). No copper/oil ID in the top 20. |

No Hugging Face **model** returned by MCP claimed **HG / copper
futures** or **WTI/Brent** as the training target. Copper on the Hub
is a name collision or a **foreign price CSV**, not a copper TSFM.

---

## Official TSFMs (weights on HF; not asset-specific)

Cards / listings only. Fine-tune rights and pretraining mix vary.

| ID / code | What MCP / the card or this repo says | Fine-tune | Use here |
| --------- | ------------------------------------- | --------- | -------- |
| [amazon/chronos-2](https://hf.co/amazon/chronos-2) | MCP `hub_repo_details`: T5, 119.5M, Apache-2.0, pretrain datasets `autogluon/chronos_datasets` + `Salesforce/GiftEvalPretrain`, arXiv 2403.07815 / 2510.15821. Also [autogluon/chronos-2](https://hf.co/autogluon/chronos-2). | unknown — read that card before use | Sealed vs ridge. Same Ch13 contamination rule. |
| [amazon/chronos-bolt-base](https://hf.co/amazon/chronos-bolt-base) | MCP: T5, 205.3M, Apache-2.0. Companion: [amazon-science/chronos-forecasting](https://github.com/amazon-science/chronos-forecasting). Card: AutoGluon “offers effortless fine-tuning.” | Card yes (AutoGluon) | Already in Ch13 `09`. Sealed vs ridge. |
| [google/timesfm-2.5-200m-pytorch](https://hf.co/google/timesfm-2.5-200m-pytorch) | MCP: timesfm, 231.3M, Apache-2.0, arXiv 2310.10688. | unknown here | Sealed only |
| [google/timesfm-3.0-pytorch](https://hf.co/google/timesfm-3.0-pytorch) | MCP: 330.7M, **license:other**. | unknown here | Sealed only; license is not Apache |
| [Salesforce/moirai-2.0-R-small](https://hf.co/Salesforce/moirai-2.0-R-small) | MCP search `moirai`: also `1.0-R-*`, `1.1-R-*`, `moirai-moe-1.0-R-*`. **cc-by-nc-4.0**. | unknown here | Sealed only. NC — not a live book. |
| [ibm-granite/granite-timeseries-ttm-r2](https://hf.co/ibm-granite/granite-timeseries-ttm-r2) | MCP `author=ibm-granite` + TSFM filter: also `ttm-r1`, `ttm-r3`, `granite-timeseries-patchtst`, `patchtst-fm-r1/r2`, `flowstate-r1`. Ch13 `09` already runs **TinyTimeMixer**. | unknown here | Prefer the Ch13 notebook path |
| [NeoQuasar/Kronos-base](https://hf.co/NeoQuasar/Kronos-base) | MCP: tags `Finance` / `Candlestick` / `K-line`, MIT, 102.3M, arXiv 2508.02739. Family also `Kronos-small`, `Kronos-mini`, tokenizers. **Not** copper/oil-named. | unknown here | Sealed only if Engine opens a candlestick hyp. Do not swap Cell 1. |
| [time-series-foundation-models/Lag-Llama](https://huggingface.co/time-series-foundation-models/Lag-Llama) | On TSFM tag (web listing 2026-09-20); **not** re-fetched via MCP this pass | unknown here | Sealed only |
| [NX-AI/TiRex](https://huggingface.co/NX-AI/TiRex) / TiRex-2 | Same: TSFM tag listing, not MCP-refetched | unknown here | Sealed only |
| Datadog Toto | TSFM tag: `Datadog/Toto-2.0-2.5B`, `Toto-Open-Base-1.0` — not MCP-refetched | unknown here | Sealed only |

**DLinear / PatchTST (from-scratch, this fork):** Ch13 `03_great_debate` /
`04_transformers`; upstream [cure-lab/LTSF-Linear](https://github.com/cure-lab/LTSF-Linear),
[PatchTST/PatchTST](https://github.com/PatchTST/PatchTST). These are
architectures, not copper/oil checkpoints.

---

## Finance-pretrained TSFM (closest “fine-tune for assets” hit)

| ID | Card (fetched 2026-09-20) | Fit |
| -- | ------------------------- | --- |
| [LG-AI-Research/EXAONE-Forecast-for-Finance-1.0](https://hf.co/LG-AI-Research/EXAONE-Forecast-for-Finance-1.0) | MCP: task `time-series-forecasting`, tags `finance` / `attention-free` / `zero-shot`, license **other**, arXiv 2609.04239. Card (fetched earlier 2026-09-20): 202M, CNN+MLP, pretrained on **synthetic** financial series; zero-shot on **FinVerse** (FX, **commodities**, crypto, FI, equities, ETFs, macro). Code: [LGAI-Research/EXAONE-Forecast](https://github.com/LGAI-Research/EXAONE-Forecast). Weights **EXAONE AI Model License 1.2-NC**. Card: **“Only zero-shot performance is reported. Fine-tuning and ensembling are untested.”** | Sealed zero-shot on the **named** Friday/`CL=F`/`BZ=F` series only. Do not treat FinVerse “commodities” as our panel. Do not use commercially. |

---

## Oil-specific (text / series, not a return GNN)

From Tavily run `55711173-…` plus cards fetched where noted.

| ID | What the source says | Use here |
| -- | -------------------- | -------- |
| [Captain-1337/CrudeBERT](https://hf.co/Captain-1337/CrudeBERT) | MCP: `text-classification`, BERT, arXiv 1908.10063 / 2305.06140. Card: FinBERT fine-tuned on crude headlines; WTI-oriented. Thesis/code: [github.com/Captain-1337/Master-Thesis](https://github.com/Captain-1337/Master-Thesis). Card: FinBERT alone had “little or hardly any significance” for crude; **further research required** before using CrudeBERT to predict oil prices. | Oil **text** sidecar only. Not a substitute for the EIA logistic CONTINUE. Semantics counts stay SHELF. |
| [polibert/oil-sentiment-headlines](https://hf.co/datasets/polibert/oil-sentiment-headlines) | MCP `hub_repo_details`: card says 18,450 WTI/Brent headlines; viewer split `default/train` is **11.1K** rows × 8 cols (`date`, `headline`, `source`, `direction`, `relevance_score`, `magnitude_score`, …). CC-BY-4.0. | Dataset only. Do not join onto the oil lock panel without a PIT card. |
| [newsdata01/crude-oil-and-petroleum-market-news-dataset](https://huggingface.co/datasets/newsdata01/crude-oil-and-petroleum-market-news-dataset) | Tavily: news snapshot covering Brent/WTI. | Same |
| [iizy/calcfi-open-data](https://huggingface.co/datasets/iizy/calcfi-open-data) | Tavily: Energy category includes `crude-oil-wti`, `crude-oil-brent`. | Foreign series. Do not replace `CL=F`/`BZ=F` or `oil_panel_eia_v1_1`. |
| [CommerAI/tirex-multidomain-forecaster](https://huggingface.co/CommerAI/tirex-multidomain-forecaster) | Tavily: fine-tuned TiRex; card claims Energy & Utilities datasets in FEV-Bench. | Sealed only if Engine opens it. Not an oil lock. |

Oil lock in this repo remains `NYMEX_CL` / `ICE_BRENT` / `CL=F` / `BZ=F`.
Kaggle `WTIOIL-PERP` ≠ that lock ([RECEIPT](RECEIPT_2026-09-20_KAGGLE.md)).

---

## Copper-specific

| Source | Status |
| ------ | ------ |
| MCP `copper futures forecast` / TSFM+commodity query | **No repositories** |
| MCP `copper` model list | No HG/CME TSFM. Hits are name collisions. |
| [Farmaanaa/global_copper_price_daily](https://hf.co/datasets/Farmaanaa/global_copper_price_daily) | MCP: daily Yahoo Finance copper, USD/lb, 6.5K rows (`mart` + `observations`), CC-BY-4.0. **Foreign.** Not `HG=F` Friday. Do not mix into sha `35f1fce22bca`. |
| Tavily `55711173-…` | “No explicit HF dataset or model … mentions copper (HG) by name.” (dataset row above is a **price CSV**, not a model.) |
| Li (2026) *A Hybrid Model for Copper Futures Price Forecasting*, [Entropy 28(3):320](https://www.mdpi.com/1099-4300/28/3/320) | Already in [GNN_RESOURCE_MAP.md](GNN_RESOURCE_MAP.md). Literature, not a HF weight. |
| [paperswithbacktest/Commodities-Daily-Price](https://hf.co/datasets/paperswithbacktest/Commodities-Daily-Price) | MCP: **gated**. Viewer 404 with current OAuth. Card: 508,406 rows / 63 symbols. **Foreign.** Do not mix. |
| [lynx1231/historical-commodity-futures-data-sample](https://hf.co/datasets/lynx1231/historical-commodity-futures-data-sample) | MCP card: precious metals + ag sample. Preview `daily/train` rows 0–14 are **COMEX Gold** `GCF26` only. Copper not in that preview. |

There is **no** open copper-HG TSFM checkpoint in the sources above.
Copper “fine-tune” here means: sealed Chronos / EXAONE / TTM **on our
Friday `fwd_ret_5d`**, or the existing TinyGAT cell — not a new panel.

---

## Gold / silver HF models (not our assets)

MCP `hub_repo_details` confirms [AurelPx/Argent-1D](https://hf.co/AurelPx/Argent-1D)
(tags: `silver`, `commodities`, `research-only`) and
[AurelPx/Aurum-1D](https://hf.co/AurelPx/Aurum-1D) (tags: `gold`,
`commodities`, `research-only`). They are **not** copper or oil. Do
not port them onto HG/CL.

---

## Fine-tune vs scratch (quoted, not inferred)

| Source | Statement |
| ------ | --------- |
| Chronos-Bolt card | AutoGluon “offers effortless fine-tuning of Chronos models” and covariate regressors. |
| EXAONE Finance card | “Only zero-shot performance is reported. Fine-tuning and ensembling are untested.” |
| CrudeBERT card | Domain adaptation (supply/demand headlines) was required; generic FinBERT did not transfer to crude. |
| Ch13 README | Foundation-model adaptation has a **finance transfer gap**; pretraining is a leakage channel **no temporal split can inspect**. |

---

## Allowed next use (if Engine opens it)

1. Keep Cell 1 TinyGAT running. Do not swap in a TSFM mid-cell.
2. After Cell 1 stamps: optional **sealed** Ch13 `09` / Chronos-Bolt or
   EXAONE **zero-shot** on the same Friday `fwd_ret_5d` (copper) or
   `oil_panel_eia_v1_1` `fwd_ret_5d` (oil). Name the checkpoint + sha
   on the receipt.
3. Chronos **fine-tune** only via AutoGluon if Engine freezes a hyp;
   still vs MOM, still `promote=false`.
4. CrudeBERT only as a **headline** feature with event/disclosure/
   extract timestamps — not as a price model.

## Hard do-nots

- Mix HF commodity CSVs into the copper or oil registry hash
- Treat EXAONE NC weights as a live or paper book
- Treat FinVerse / FEV-Bench ranks as our S2 gate
- Fine-tune CrudeBERT and call it an oil lock
- Invent a copper HF checkpoint that this search did not list
