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
    try:
        # Map user symbol to Yahoo Finance symbol
        yf_symbol = SYMBOL_MAP.get(symbol, symbol)
        
        # Fetch 15-minute data
        df = yf.download(
            yf_symbol,
            interval="15m",
            period=f"{lookback_days}d",
            auto_adjust=False,
            progress=False,
        )
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Handle MultiIndex columns (for single symbol, should be flat)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            df.columns = df.columns.get_level_values(0)
        
        # Select OHLC columns and normalize to lowercase
        df = df[["Open", "High", "Low", "Close"]].copy()
        df.columns = ["open", "high", "low", "close"]
        
        # Clean: remove NaN, sort by time
        df.dropna(inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
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
    
    if df_15m.empty:
        return {"15M": df_15m, "1H": pd.DataFrame(), "4H": pd.DataFrame()}
    
    # Ensure timezone is UTC
    if df_15m.index.tz is None:
        df_15m.index = df_15m.index.tz_localize("UTC")
    
    # Resample to 1H and 4H
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
