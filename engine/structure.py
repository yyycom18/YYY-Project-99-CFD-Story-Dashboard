"""
Structure break and swing (fractal) detection.
Engine uses raw UTC data only. No timezone conversion.
Structure break valid only if: close beyond confirmed swing, body > 1.5x avg, not wick-only.
Swing = fractal 2-left, 2-right default.
"""
from typing import List, Optional, Tuple

import pandas as pd
import numpy as np

# Fractal left/right bars
FRACTAL_LEFT = 2
FRACTAL_RIGHT = 2
BODY_AVG_N = 20
STRUCTURE_BODY_MULTIPLIER = 1.5


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to uppercase (Open, High, Low, Close) for engine compatibility."""
    if df is None or df.empty:
        return df
    # Create mapping: lowercase/mixed case → uppercase
    m = {}
    for c in df.columns:
        c_lower = c.lower()
        if c_lower == "open":
            m[c] = "Open"
        elif c_lower == "high":
            m[c] = "High"
        elif c_lower == "low":
            m[c] = "Low"
        elif c_lower == "close":
            m[c] = "Close"
    return df.rename(columns=m) if m else df


def _body_size(series: pd.Series) -> pd.Series:
    return (series["Close"] - series["Open"]).abs()


def _avg_body(df: pd.DataFrame, n: int = BODY_AVG_N) -> pd.Series:
    body = _body_size(df)
    return body.rolling(window=n, min_periods=1).mean()


def detect_swing_highs(df: pd.DataFrame, left: int = FRACTAL_LEFT, right: int = FRACTAL_RIGHT) -> pd.Series:
    """
    Fractal swing highs: high at index i is swing iff
    high[i] >= high[i-k] for k in 1..left and high[i] >= high[i+k] for k in 1..right.
    Returns boolean series True at swing high bars.
    """
    df = _normalize_columns(df)  # Ensure uppercase column names
    high = df["High"].values
    n = len(high)
    out = np.zeros(n, dtype=bool)
    for i in range(left, n - right):
        if i < left or i + right >= n:
            continue
        ok = True
        for k in range(1, left + 1):
            if high[i] < high[i - k]:
                ok = False
                break
        if not ok:
            continue
        for k in range(1, right + 1):
            if high[i] < high[i + k]:
                ok = False
                break
        out[i] = ok
    return pd.Series(out, index=df.index)


def detect_swing_lows(df: pd.DataFrame, left: int = FRACTAL_LEFT, right: int = FRACTAL_RIGHT) -> pd.Series:
    """Fractal swing lows. Returns boolean series True at swing low bars."""
    df = _normalize_columns(df)  # Ensure uppercase column names
    low = df["Low"].values
    n = len(low)
    out = np.zeros(n, dtype=bool)
    for i in range(left, n - right):
        if i < left or i + right >= n:
            continue
        ok = True
        for k in range(1, left + 1):
            if low[i] > low[i - k]:
                ok = False
                break
        if not ok:
            continue
        for k in range(1, right + 1):
            if low[i] > low[i + k]:
                ok = False
                break
        out[i] = ok
    return pd.Series(out, index=df.index)


def get_last_confirmed_swing_high(
    df: pd.DataFrame,
    up_to_idx: int,
    swing_highs: Optional[pd.Series] = None,
) -> Optional[float]:
    """Last confirmed swing high strictly before bar index up_to_idx. Pass swing_highs to avoid recomputing."""
    df = _normalize_columns(df)  # Ensure uppercase column names
    if swing_highs is None:
        swing_highs = detect_swing_highs(df)
    for i in range(up_to_idx - 1, -1, -1):
        if i < len(swing_highs) and swing_highs.iloc[i]:
            return float(df["High"].iloc[i])
    return None


def get_last_confirmed_swing_low(
    df: pd.DataFrame,
    up_to_idx: int,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[float]:
    """Last confirmed swing low strictly before bar index up_to_idx. Pass swing_lows to avoid recomputing."""
    df = _normalize_columns(df)  # Ensure uppercase column names
    if swing_lows is None:
        swing_lows = detect_swing_lows(df)
    for i in range(up_to_idx - 1, -1, -1):
        if i < len(swing_lows) and swing_lows.iloc[i]:
            return float(df["Low"].iloc[i])
    return None


def is_structure_break_up(
    df: pd.DataFrame,
    i: int,
    body_mult: float = STRUCTURE_BODY_MULTIPLIER,
    avg_n: int = BODY_AVG_N,
    swing_highs: Optional[pd.Series] = None,
) -> bool:
    """
    True if bar i is a valid upside structure break:
    - Close above previous confirmed swing high
    - Body size > body_mult * average body (last avg_n)
    - Not wick-only break (close must be above swing)
    """
    df = _normalize_columns(df)  # Ensure uppercase column names
    if i < 1:
        return False
    swing_high = get_last_confirmed_swing_high(df, i, swing_highs=swing_highs)
    if swing_high is None:
        return False
    row = df.iloc[i]
    close = row["Close"]
    open_ = row["Open"]
    if close <= swing_high:
        return False
    body = abs(close - open_)
    avg_b = _avg_body(df, avg_n).iloc[i] if i < len(df) else body
    if avg_b <= 0:
        avg_b = body
    if body < body_mult * avg_b:
        return False
    return True


def is_structure_break_down(
    df: pd.DataFrame,
    i: int,
    body_mult: float = STRUCTURE_BODY_MULTIPLIER,
    avg_n: int = BODY_AVG_N,
    swing_lows: Optional[pd.Series] = None,
) -> bool:
    """
    True if bar i is a valid downside structure break:
    - Close below previous confirmed swing low
    - Body size > body_mult * average body
    """
    df = _normalize_columns(df)  # Ensure uppercase column names
    if i < 1:
        return False
    swing_low = get_last_confirmed_swing_low(df, i, swing_lows=swing_lows)
    if swing_low is None:
        return False
    row = df.iloc[i]
    close = row["Close"]
    open_ = row["Open"]
    if close >= swing_low:
        return False
    body = abs(close - open_)
    avg_b = _avg_body(df, avg_n).iloc[i] if i < len(df) else body
    if avg_b <= 0:
        avg_b = body
    if body < body_mult * avg_b:
        return False
    return True
