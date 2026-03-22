"""
Market data fetching via yfinance. Real market data only (no synthesis).
Fetches 15-minute OHLC data for CFDs via Yahoo Finance.
"""
import pandas as pd
import yfinance as yf


# Symbol mapping: User-friendly name → Yahoo Finance symbol
SYMBOL_MAP = {
    "XAUUSD": "GC=F",        # Gold futures (COMEX)
    "EURUSD": "EURUSD=X",    # EUR/USD pair
    "AUDUSD": "AUDUSD=X",    # AUD/USD pair
    "GBPUSD": "GBPUSD=X",    # GBP/USD pair
    "USDCAD": "USDCAD=X",    # USD/CAD pair
    "NZDUSD": "NZDUSD=X",    # NZD/USD pair
    "USDCHF": "USDCHF=X",    # USD/CHF pair
    "USDJPY": "USDJPY=X",    # USD/JPY pair
    "HK50": "^HSI",          # Hang Seng Index
}


def fetch_15m_data(symbol: str, lookback_days: int = 15) -> pd.DataFrame:
    """
    Fetch 15-minute OHLC data using yfinance.
    
    Args:
        symbol: User-friendly asset name (e.g., "XAUUSD")
        lookback_days: Number of days to fetch (default 15 = 2 weeks)
    
    Returns:
        DataFrame with columns: open, high, low, close (lowercase)
        Index: datetime (UTC)
    """
    # Debug: symbol mapping and request info
    print(f"DEBUG fetch_15m_data: requested symbol={symbol}, lookback_days={lookback_days}")
    yf_symbol = SYMBOL_MAP.get(symbol, symbol)
    print(f"DEBUG fetch_15m_data: mapped to yf_symbol={yf_symbol}")

    # Ensure Yahoo period cap for 15m interval (Yahoo typically limits to ~60 days for 15m)
    max_period = 60
    period_days = min(lookback_days, max_period)

    # Try download with retries and fallback smaller windows
    attempts = [period_days, min(period_days, 30), 14, 7, 3]
    tried = set()
    # Alternate symbol fallbacks for known symbols
    alternates_map = {
        "XAUUSD": ["XAUUSD=X", "GC=F"],
        "HK50": ["^HSI"],
    }
    for days in attempts:
        if days in tried:
            continue
        tried.add(days)
        period_arg = f"{days}d"
        try:
            print(f"DEBUG fetch_15m_data: attempting yf.download({yf_symbol}, interval='15m', period='{period_arg}')")
            df = yf.download(
                yf_symbol,
                interval="15m",
                period=period_arg,
                auto_adjust=False,
                progress=False,
            )
            print(f"DEBUG fetch_15m_data: raw download type={type(df)}")
            if df is None or df.empty:
                print(f"DEBUG fetch_15m_data: download returned empty for period={period_arg}")
                # Try alternate Yahoo symbols if available
                alt_list = alternates_map.get(symbol, []) if symbol in alternates_map else alternates_map.get(yf_symbol, [])
                tried_alt = False
                for alt in alt_list:
                    try:
                        print(f"DEBUG fetch_15m_data: attempting alternate symbol {alt} for period={period_arg}")
                        df_alt = yf.download(alt, interval="15m", period=period_arg, auto_adjust=False, progress=False)
                        if df_alt is None or df_alt.empty:
                            print(f"DEBUG fetch_15m_data: alternate {alt} returned empty")
                            continue
                        # success with alternate
                        df = df_alt
                        tried_alt = True
                        print(f"DEBUG fetch_15m_data: alternate {alt} succeeded")
                        break
                    except Exception as e:
                        print(f"DEBUG fetch_15m_data: alternate {alt} download exception: {e}")
                if not tried_alt:
                    df = pd.DataFrame()
            else:
                # Handle MultiIndex columns (for single symbol, should be flat)
                if isinstance(df.columns, pd.MultiIndex):
                    df = df.copy()
                    df.columns = df.columns.get_level_values(0)
                # Show head and shape for debugging
                try:
                    print("DEBUG fetch_15m_data: head:\n", df.head())
                except Exception:
                    pass
                print("DEBUG fetch_15m_data: shape:", getattr(df, "shape", None))
                # Normalize columns if present
                cols_upper = [c for c in df.columns]
                expected = ["Open", "High", "Low", "Close"]
                if all(c in df.columns for c in expected):
                    df = df[["Open", "High", "Low", "Close"]].copy()
                    df.columns = ["open", "high", "low", "close"]
                else:
                    # try lowercase
                    expected_l = ["open", "high", "low", "close"]
                    if all(c in df.columns for c in expected_l):
                        df = df[expected_l].copy()
                    else:
                        # columns not matching, keep as-is but warn
                        print("DEBUG fetch_15m_data: unexpected columns:", df.columns.tolist())
                # Clean: remove NaN, sort by time
                df.dropna(inplace=True)
                # Ensure datetime index
                try:
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)
                except Exception:
                    print("DEBUG fetch_15m_data: failed to coerce index to DatetimeIndex")
                df.sort_index(inplace=True)
            # If non-empty, return
            if not df.empty:
                return df
        except Exception as e:
            print(f"DEBUG fetch_15m_data: download exception for period={period_arg}: {e}")
            df = pd.DataFrame()

    # All attempts failed — return empty DataFrame but log clearly
    print(f"ERROR fetch_15m_data: unable to fetch 15m data for {symbol} after retries.")
    return pd.DataFrame()


def fetch_all_timeframes(symbol: str, lookback_days: int = 15) -> dict:
    """
    Fetch 15M data and resample to 1H and 4H.
    
    Args:
        symbol: User-friendly asset name
        lookback_days: Number of days to fetch
    
    Returns:
        Dict with keys "15M", "1H", "4H", each containing a DataFrame
    """
    df_15m = fetch_15m_data(symbol, lookback_days)
    if df_15m is None or df_15m.empty:
        print(f"ERROR fetch_all_timeframes: 15M data empty for {symbol}. Aborting fetch_all_timeframes.")
        return {"15M": pd.DataFrame(), "1H": pd.DataFrame(), "4H": pd.DataFrame()}
    
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
