"""
Market data fetching via yfinance. Real market data only (no synthesis).
Fetches 15-minute OHLC data for CFDs via Yahoo Finance.
"""
from typing import Optional

import pandas as pd
import yfinance as yf


# Symbol mapping: User-friendly name → Yahoo Finance symbol (order = sidebar / scanner order)
SYMBOL_MAP = {
    "XAUUSD": "GC=F",        # Gold futures (COMEX); XAUUSD=X fallback via YFIN_SYMBOL_FALLBACKS
    "GBPJPY": "GBPJPY=X",
    "EURJPY": "EURJPY=X",
    "EURUSD": "EURUSD=X",
    "EURGBP": "EURGBP=X",
    "AUDUSD": "AUDUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "USDCHF": "USDCHF=X",
    "USDJPY": "USDJPY=X",
    "HK50": "^HSI",
}

# Ordered Yahoo symbols to try per asset (spot/CFD proxy first, then futures/alternates)
YFIN_SYMBOL_FALLBACKS = {
    # GC=F is the reliable 15m source for XAUUSD; avoid XAUUSD=X retries which are unreliable.
    "XAUUSD": ["GC=F"],
    "HK50": ["^HSI"],
}

# Explicit supported source map (used as capability hint; does not change engine)
SUPPORTED_SOURCES = {
    "XAUUSD": ["GC=F"],
}

REQUIRED_OHLC = ("open", "high", "low", "close")


def _yahoo_symbols_to_try(asset_key: str) -> list:
    if asset_key in YFIN_SYMBOL_FALLBACKS:
        return list(YFIN_SYMBOL_FALLBACKS[asset_key])
    return [SYMBOL_MAP.get(asset_key, asset_key)]


def normalize_ohlc_dataframe(df: pd.DataFrame, *, debug_label: str = "") -> pd.DataFrame:
    """
    Flatten yfinance columns, lowercase names, enforce open/high/low/close.
    Raises ValueError if data is empty or OHLC is incomplete.
    """
    if df is None or df.empty:
        raise ValueError("Empty DataFrame from data source")

    print("DEBUG RAW DF:")
    print(type(df))
    print(df.head())
    print(df.columns)

    out = df.copy()

    if isinstance(out.columns, pd.MultiIndex):
        lev0 = [str(x) for x in out.columns.get_level_values(0)]
        lev1 = (
            [str(x) for x in out.columns.get_level_values(1)] if out.columns.nlevels > 1 else []
        )
        ohlc_like = {"open", "high", "low", "close", "adj close", "volume"}
        l0 = {x.lower().strip() for x in lev0}
        l1 = {x.lower().strip() for x in lev1} if lev1 else set()
        if l0 & ohlc_like:
            out.columns = lev0
        elif l1 & ohlc_like:
            out.columns = lev1
        else:
            out.columns = lev0

    out.columns = [str(c).strip().lower() for c in out.columns]

    if "close" not in out.columns and "adj close" in out.columns:
        out = out.rename(columns={"adj close": "close"})

    missing = [c for c in REQUIRED_OHLC if c not in out.columns]
    if missing:
        raise ValueError(
            f"Missing OHLC columns {missing}; columns={list(out.columns)} {debug_label}".strip()
        )

    out = out[list(REQUIRED_OHLC)].copy()
    out.dropna(inplace=True)
    if out.empty:
        raise ValueError("Empty DataFrame after OHLC subset and dropna")

    if not isinstance(out.index, pd.DatetimeIndex):
        out.index = pd.to_datetime(out.index)
    out.sort_index(inplace=True)
    return out


def fetch_15m_data(symbol: str, lookback_days: int = 15) -> pd.DataFrame:
    """
    Fetch 15-minute OHLC data using yfinance.
    
    Args:
        symbol: User-friendly asset name (e.g., "XAUUSD")
        lookback_days: Number of days to fetch (default 15 = 2 weeks)
    
    Returns:
        DataFrame with columns: open, high, low, close (lowercase)
        Index: datetime (UTC)
    
    Raises:
        ValueError: If no valid OHLC data could be obtained after retries.
    """
    print(f"DEBUG fetch_15m_data: requested symbol={symbol}, lookback_days={lookback_days}")
    yahoo_chain = _yahoo_symbols_to_try(symbol)
    print(f"DEBUG fetch_15m_data: Yahoo symbol chain={yahoo_chain}")

    max_period = 60
    period_days = min(lookback_days, max_period)

    attempts = [period_days, min(period_days, 30), 14, 7, 3]
    tried_days = set()
    last_error: Optional[Exception] = None

    for days in attempts:
        if days in tried_days:
            continue
        tried_days.add(days)
        period_arg = f"{days}d"

        for yf_sym in yahoo_chain:
            try:
                print(
                    f"DEBUG fetch_15m_data: yf.download({yf_sym}, interval='15m', period='{period_arg}')"
                )
                raw = yf.download(
                    yf_sym,
                    interval="15m",
                    period=period_arg,
                    auto_adjust=False,
                    progress=False,
                    timeout=10,  # enforce faster failure for unreliable sources
                )
                print(f"DEBUG fetch_15m_data: raw download type={type(raw)}, shape={getattr(raw, 'shape', None)}")
                if raw is None or raw.empty:
                    print(f"DEBUG fetch_15m_data: empty raw for {yf_sym} period={period_arg}")
                    continue
                label = f"[{symbol} yf={yf_sym} period={period_arg}]"
                df = normalize_ohlc_dataframe(raw, debug_label=label)
                print(f"DEBUG fetch_15m_data: normalized OK {label} rows={len(df)}")
                return df
            except ValueError as e:
                last_error = e
                print(f"DEBUG fetch_15m_data: normalize failed {yf_sym} period={period_arg}: {e}")
                continue
            except Exception as e:
                last_error = e
                print(f"DEBUG fetch_15m_data: download exception {yf_sym} period={period_arg}: {e}")
                continue

    msg = f"Unable to fetch valid 15m OHLC for {symbol} after retries."
    if last_error:
        msg += f" Last error: {last_error}"
    print(f"ERROR fetch_15m_data: {msg}")
    raise ValueError(msg)


def fetch_all_timeframes(symbol: str, lookback_days: int = 15) -> dict:
    """
    Fetch 15M data and resample to 1H and 4H.
    
    Args:
        symbol: User-friendly asset name
        lookback_days: Number of days to fetch
    
    Returns:
        Dict with keys "15M", "1H", "4H", each containing a DataFrame
    
    Raises:
        ValueError: Propagated from fetch_15m_data if OHLC cannot be obtained.
    """
    df_15m = fetch_15m_data(symbol, lookback_days)
    if df_15m is None or df_15m.empty:
        raise ValueError(f"fetch_all_timeframes: 15M data empty for {symbol} after fetch_15m_data.")
    
    # Ensure datetime index and timezone is UTC
    try:
        if not isinstance(df_15m.index, pd.DatetimeIndex):
            df_15m.index = pd.to_datetime(df_15m.index)
    except Exception:
        print("DEBUG fetch_all_timeframes: failed to parse datetime index for 15M")
    if getattr(df_15m.index, "tz", None) is None:
        try:
            df_15m.index = df_15m.index.tz_localize("UTC")
        except Exception:
            try:
                df_15m.index = df_15m.index.tz_convert("UTC")
            except Exception:
                print("DEBUG fetch_all_timeframes: could not set timezone to UTC for 15M index")
    
    # Resample to 1H and 4H
    # Resample to 1H and 4H if sufficient data
    if len(df_15m) < 50:
        print(f"WARNING fetch_all_timeframes: only {len(df_15m)} rows in 15M for {symbol}; skipping resample")
        return {"15M": df_15m, "1H": pd.DataFrame(), "4H": pd.DataFrame()}

    df_1h = df_15m.resample("1h").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    }).dropna()
    
    df_4h = df_15m.resample("4h").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    }).dropna()
    
    return {
        "15M": df_15m,
        "1H": df_1h,
        "4H": df_4h,
    }
