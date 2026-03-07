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
        df = df.sort_index()
        df = df[~df.index.duplicated(keep="first")]
        return df
    except Exception:
        return None


# Realistic base price and typical range (volatility) per asset. Do not normalize.
_ASSET_BASE_PRICE = {
    "XAUUSD": (5100.0, 50.0),   # Gold (e.g. 51.00 * 100); move ~50
    "EURUSD": (1.0650, 0.0040),
    "AUDUSD": (0.6520, 0.0025),
    "GBPUSD": (1.2650, 0.0050),
    "USDCAD": (1.3600, 0.0040),
    "NZDUSD": (0.6020, 0.0025),
    "USDCHF": (0.8820, 0.0030),
    "USDJPY": (149.50, 1.20),
    "HK50": (17000.0, 150.0),
}


def generate_sample_ohlc(
    asset: str,
    timeframe: str,
    bars: int = 500,
    freq: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generate sample OHLC for development when no CSV exists.
    Uses realistic market ranges per asset (no normalization).
    Index is UTC. Columns: Open, High, Low, Close.
    
    OHLC logic:
    - Close follows a mean-reverting random walk
    - Open = previous close + small gap
    - High = max(Open, Close) + random intrabar movement
    - Low = min(Open, Close) - random intrabar movement
    
    This ensures High >= max(Open,Close) and Low <= min(Open,Close), like real markets.
    """
    if freq is None:
        freq = {"15M": "15min", "1H": "1h", "4H": "4h"}.get(timeframe, "1h")
    import numpy as np
    base, vol = _ASSET_BASE_PRICE.get(asset, (100.0, 1.0))
    rng = pd.date_range(end=pd.Timestamp.now("UTC"), periods=bars, freq=freq)
    np.random.seed(hash(asset) % 2**32)
    
    # Generate realistic close prices (mean-reverting random walk)
    steps = np.random.randn(bars) * (vol * 0.08)
    close = base + np.cumsum(steps - np.mean(steps) * 0.1)  # Mild mean reversion
    
    # Generate open prices (previous close + small gap)
    open_ = np.roll(close, 1)
    open_[0] = close[0]  # First open = first close
    
    # Generate realistic high/low (intrabar movement around open/close)
    # High always >= max(Open, Close)
    # Low always <= min(Open, Close)
    intrabar_range = np.abs(np.random.randn(bars)) * (vol * 0.35)  # Intrabar wick size
    intrabar_high = np.abs(np.random.randn(bars)) * (vol * 0.4)     # How much high extends
    intrabar_low = np.abs(np.random.randn(bars)) * (vol * 0.4)      # How much low extends
    
    oc_high = np.maximum(open_, close)  # Highest of Open/Close
    oc_low = np.minimum(open_, close)   # Lowest of Open/Close
    
    high = oc_high + intrabar_high
    low = np.maximum(oc_low - intrabar_low, base * 0.90)  # Floor at 90% of base
    
    # Ensure High >= Low and proper OHLC relationships
    high = np.maximum(high, low + vol * 0.1)  # High must be at least vol*0.1 above low
    
    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close},
        index=rng,
    )
    # Ensure UTC timezone safely (rng from date_range(..., tz=UTC) is already tz-aware)
    if getattr(df.index, "tz", None) is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    return df


def fetch_data(asset: str, timeframe: str, bars: int = 1000) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC for one asset/timeframe. Returns raw UTC only.
    Tries CSV first; falls back to sample data for development.
    """
    df = load_ohlc_csv(asset, timeframe)
    if df is not None:
        df = df.tail(bars) if len(df) > bars else df
    else:
        df = generate_sample_ohlc(asset, timeframe, bars=bars)
    if df is not None and not df.empty:
        df = df.sort_index()
        df = df[~df.index.duplicated(keep="first")]
    return df


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
    if getattr(df_15m.index, "tz", None) is None:
        df_15m.index = df_15m.index.tz_localize("UTC")
    else:
        df_15m.index = df_15m.index.tz_convert("UTC")
    out["1H"] = df_15m.resample("1h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    out["4H"] = df_15m.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    return out
