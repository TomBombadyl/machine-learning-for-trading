#!/usr/bin/env python3
"""Resolve or build the copper Friday research panel.

**NOT A PROMOTE.** Prefer the Engine Friday parquet. Else build a
yfinance ``HG=F`` Friday grid and say so on the receipt. Never mix
Databento HG and ``HG=F`` in one hash.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

from contract import COPPER_ROOT, EXPECTED_FRIDAY_SHA12, FRIDAY_PANEL

PROMOTE = False
YF_TICKERS = {
    "HG": "HG=F",
    "CPER": "CPER",
    "COPX": "COPX",
    "FCX": "FCX",
}
COT_LAG_DAYS = 6


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def panel_candidates() -> list[Path]:
    env = os.environ.get("DEEP_TEST_PANEL")
    extra = Path(env) if env else None
    return [
        extra,
        FRIDAY_PANEL,
        COPPER_ROOT / "deep_test_friday_panel_v0.parquet",
        Path(
            "/kaggle/input/datasets/synapgarden/synap-finpredict-panels-v0/"
            "deep_test_friday_panel_v0.parquet"
        ),
        Path("/kaggle/input/synap-finpredict-panels-v0/deep_test_friday_panel_v0.parquet"),
    ]


def resolve_existing_panel() -> Path | None:
    for candidate in panel_candidates():
        if candidate is not None and candidate.is_file():
            return candidate
    kaggle_in = Path("/kaggle/input")
    if kaggle_in.exists():
        hits = sorted(kaggle_in.rglob("deep_test_friday_panel_v0.parquet"))
        if hits:
            return hits[0]
    return None


def _trading_mom(close: pd.Series, window: int) -> pd.Series:
    return close / close.shift(window) - 1.0


def _fwd_ret(close: pd.Series, horizon: int) -> pd.Series:
    return close.shift(-horizon) / close - 1.0


def build_yfinance_friday_panel(start: str = "2000-01-01") -> pd.DataFrame:
    if yf is None:
        raise ImportError("yfinance is required to build the free Friday fallback panel")
    frames = []
    for name, ticker in YF_TICKERS.items():
        raw = yf.download(ticker, start=start, auto_adjust=True, progress=False)
        if raw is None or raw.empty:
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [str(col[0]).lower() for col in raw.columns]
        else:
            raw.columns = [str(col).lower() for col in raw.columns]
        if "close" not in raw.columns:
            continue
        piece = raw[["close"]].rename(columns={"close": f"close_{name.lower()}"})
        frames.append(piece)
    if not frames:
        raise FileNotFoundError("yfinance returned no copper-family closes")
    daily = pd.concat(frames, axis=1).sort_index()
    daily.index = pd.to_datetime(daily.index).tz_localize(None)
    close_hg = daily["close_hg"]
    daily["mom_5d"] = _trading_mom(close_hg, 5)
    daily["mom_21d"] = _trading_mom(close_hg, 21)
    daily["mom_63d"] = _trading_mom(close_hg, 63)
    if "close_cper" in daily.columns:
        daily["cper_mom_21d"] = _trading_mom(daily["close_cper"], 21)
        daily["ret_cper"] = daily["close_cper"].pct_change()
    if "close_copx" in daily.columns:
        daily["copx_mom_21d"] = _trading_mom(daily["close_copx"], 21)
        daily["ret_copx"] = daily["close_copx"].pct_change()
    if "close_fcx" in daily.columns:
        daily["fcx_mom_63d"] = _trading_mom(daily["close_fcx"], 63)
        daily["ret_fcx"] = daily["close_fcx"].pct_change()
    daily["ret_hg"] = close_hg.pct_change()
    daily["fwd_ret_5d"] = _fwd_ret(close_hg, 5)
    daily["fwd_ret_21d"] = _fwd_ret(close_hg, 21)
    daily["fwd_ret_63d"] = _fwd_ret(close_hg, 63)
    friday = daily[daily.index.dayofweek == 4].copy()
    friday["date"] = friday.index
    friday = friday.reset_index(drop=True)
    return friday


def attach_local_cot(df: pd.DataFrame, cot_path: Path | None = None) -> pd.DataFrame:
    """Left-join CFTC COT with a +6 calendar-day availability lag."""
    candidates = [
        cot_path,
        COPPER_ROOT / "cot" / "HG.parquet",
        Path(os.environ["ML4T_DATA_PATH"]) / "futures" / "positioning" / "cot" / "HG.parquet"
        if os.environ.get("ML4T_DATA_PATH")
        else None,
    ]
    found = next((path for path in candidates if path is not None and path.is_file()), None)
    if found is None or "date" not in df.columns:
        return df
    cot = pd.read_parquet(found)
    date_col = "report_date" if "report_date" in cot.columns else "date"
    cot[date_col] = pd.to_datetime(cot[date_col])
    cot["cot_available"] = cot[date_col] + pd.Timedelta(days=COT_LAG_DAYS)
    keep = [col for col in cot.columns if col.startswith("cot_") or col in {date_col, "cot_available"}]
    if "cot_managed_money_net" not in cot.columns:
        long_col = next((col for col in cot.columns if "managed" in col.lower() and "long" in col.lower()), None)
        short_col = next((col for col in cot.columns if "managed" in col.lower() and "short" in col.lower()), None)
        if long_col and short_col:
            cot["cot_managed_money_net"] = cot[long_col] - cot[short_col]
            keep.append("cot_managed_money_net")
    cot = cot[keep].sort_values("cot_available")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = pd.merge_asof(
        out.sort_values("date"),
        cot.sort_values("cot_available"),
        left_on="date",
        right_on="cot_available",
        direction="backward",
    )
    out["cot_as_of"] = out.get("cot_available")
    return out


def load_or_build_panel(*, allow_yfinance: bool = True) -> tuple[pd.DataFrame, dict[str, Any]]:
    existing = resolve_existing_panel()
    if existing is not None:
        df = pd.read_parquet(existing)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        sha = sha256_file(existing)
        meta = {
            "source": "existing_parquet",
            "path": str(existing),
            "sha256": sha,
            "sha_note": (
                "matches_v0" if sha.startswith(EXPECTED_FRIDAY_SHA12) else "sha_not_v0_friday"
            ),
            "mtime_utc": datetime.fromtimestamp(existing.stat().st_mtime, tz=timezone.utc).isoformat(),
            "shape": list(df.shape),
            "promote": False,
        }
        return df, meta
    if not allow_yfinance:
        raise FileNotFoundError("Friday panel parquet not found and yfinance build disabled")
    df = build_yfinance_friday_panel()
    df = attach_local_cot(df)
    meta = {
        "source": "yfinance_HG=F_friday_build",
        "path": None,
        "sha256": None,
        "sha_note": "built_not_v0_do_not_mix_with_databento",
        "mtime_utc": datetime.now(timezone.utc).isoformat(),
        "shape": list(df.shape),
        "tickers": YF_TICKERS,
        "cot_lag_days": COT_LAG_DAYS,
        "promote": False,
    }
    return df, meta


def newey_west_t(values: np.ndarray, lags: int) -> float:
    series = np.asarray(values, dtype=float)
    series = series[np.isfinite(series)]
    n = len(series)
    if n < 8:
        return float("nan")
    mean = float(np.mean(series))
    centered = series - mean
    gamma0 = float(np.dot(centered, centered) / n)
    var = gamma0
    max_lag = max(1, min(int(lags), n - 2))
    for lag in range(1, max_lag + 1):
        weight = 1.0 - lag / (max_lag + 1)
        gamma = float(np.dot(centered[lag:], centered[:-lag]) / n)
        var += 2.0 * weight * gamma
    se = np.sqrt(max(var, 1e-18) / n)
    return float(mean / se)
