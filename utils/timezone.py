"""
Timezone utilities. Engine uses raw UTC; visualization uses Asia/Hong_Kong.
Never alter raw index before engine.
"""
from typing import Optional

import pandas as pd

VIZ_TIMEZONE = "Asia/Hong_Kong"


def convert_to_HKT(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Return a copy of the DataFrame with index converted to Asia/Hong_Kong.
    Use ONLY for visualization. Engine must receive raw UTC data.
    """
    if df is None or df.empty:
        return df
    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        return df
    try:
        if idx.tz is None:
            idx = idx.tz_localize("UTC")
        else:
            idx = idx.tz_convert("UTC")
        idx = idx.tz_convert(VIZ_TIMEZONE)
    except Exception:
        return df
    out = df.copy()
    out.index = idx
    return out


def timestamp_to_HKT_display(ts: pd.Timestamp):
    """Format timestamp for weekly table: date DDMMYYYY, time 24h HKT. Returns (date_str, time_str)."""
    try:
        if getattr(ts, "tzinfo", None) is None:
            ts = ts.tz_localize("UTC")
        dt = ts.tz_convert(VIZ_TIMEZONE)
    except Exception:
        dt = ts
    date_str = dt.strftime("%d%m%Y") if hasattr(dt, "strftime") else str(ts)[:10].replace("-", "")
    time_str = dt.strftime("%H:%M") if hasattr(dt, "strftime") else (str(ts)[11:16] if len(str(ts)) >= 16 else "")
    return date_str, time_str
