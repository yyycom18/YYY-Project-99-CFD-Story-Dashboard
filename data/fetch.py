"""
Data fetch. Returns raw UTC OHLC. No timezone conversion here.
Engine receives this raw data only.
"""
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

# Target assets and timeframes
ASSETS = [
    "XAUUSD", "GBPUSD", "EURUSD", "USDCAD",
    "NZDUSD", "AUDUSD", "USDCHF", "USDJPY", "HK50",
]
TIMEFRAMES = ["4H", "1H", "15M"]


def _ensure_utc_index(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure index is timezone-aware UTC. Do not convert to HKT."""
    if df is None or df.empty:
        return df
    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        return df
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    out = df.copy()
    out.index = idx
    return out


def load_ohlc_csv(asset: str, timeframe: str) -> Optional[pd.DataFrame]:
    """
    Load OHLC from data/raw/{asset}_{timeframe}.csv.
    Expected columns: Open, High, Low, Close (and optional Volume).
    Index = datetime. Returns raw UTC (or naive treated as UTC).
    """
    raw_dir = RAW_DIR
    filename = f"{asset}_{timeframe}.csv"
    path = raw_dir / filename
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        for c in ["Open", "High", "Low", "Close"]:
            if c not in df.columns:
                return None
        df = _ensure_utc_index(df)
        return df.sort_index()
    except Exception:
        return None


def generate_sample_ohlc(
    asset: str,
    timeframe: str,
    bars: int = 500,
    freq: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generate sample OHLC for development when no CSV exists.
    Index is UTC. Columns: Open, High, Low, Close.
    """
    if freq is None:
        freq = {"15M": "15min", "1H": "1h", "4H": "4h"}.get(timeframe, "1h")
    import numpy as np
    rng = pd.date_range(end=pd.Timestamp.now("UTC"), periods=bars, freq=freq)
    np.random.seed(hash(asset) % 2**32)
    close = 100 + np.cumsum(np.random.randn(bars) * 0.3)
    high = close + np.abs(np.random.randn(bars)) * 0.5
    low = close - np.abs(np.random.randn(bars)) * 0.5
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close},
        index=rng,
    )
    df.index = df.index.tz_localize("UTC")
    return df


def fetch_data(asset: str, timeframe: str, bars: int = 1000) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC for one asset/timeframe. Returns raw UTC only.
    Tries CSV first; falls back to sample data for development.
    """
    df = load_ohlc_csv(asset, timeframe)
    if df is not None:
        return df.tail(bars) if len(df) > bars else df
    return generate_sample_ohlc(asset, timeframe, bars=bars)


def fetch_all_timeframes(asset: str, bars_15m: int = 2000) -> Dict[str, pd.DataFrame]:
    """
    Fetch 4H, 1H, 15M for one asset. All raw UTC.
    """
    out = {}
    df_15m = fetch_data(asset, "15M", bars=bars_15m)
    if df_15m is None or df_15m.empty:
        return out
    out["15M"] = df_15m
    df_15m = df_15m.copy()
    if df_15m.index.tz is None:
        df_15m.index = df_15m.index.tz_localize("UTC")
    out["1H"] = df_15m.resample("1h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    out["4H"] = df_15m.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    return out
