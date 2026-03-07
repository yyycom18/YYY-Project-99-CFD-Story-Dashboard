"""
Zone system: Level 1 (Momentum Zone) and Level 2 (Structural Break Zone).
Engine uses raw UTC data only.
Level 1: body > 1.8x avg, wick < 30% body. No structure break required.
Level 2: Level 1 AND close beyond swing high/low AND break not fully retraced (volatility-adaptive).
"""
from typing import Optional

import pandas as pd
import numpy as np

from .structure import (
    get_last_confirmed_swing_high,
    get_last_confirmed_swing_low,
    _normalize_columns,
)

ZONE_BODY_MULTIPLIER = 1.8
ZONE_WICK_PCT_MAX = 0.30
ZONE_AVG_N = 20
ATR_WINDOW = 14
RETRACE_VOLATILITY_FACTOR = 0.8
LOOKAHEAD_BARS = 5


def _body_size(row: pd.Series) -> float:
    return abs(row["Close"] - row["Open"])


def _wick_upper(row: pd.Series) -> float:
    return row["High"] - max(row["Open"], row["Close"])


def _wick_lower(row: pd.Series) -> float:
    return min(row["Open"], row["Close"]) - row["Low"]


def _body_avg(df: pd.DataFrame, n: int = ZONE_AVG_N) -> pd.Series:
    body = df.apply(_body_size, axis=1)
    return body.rolling(window=n, min_periods=1).mean()


def is_level1_zone(
    df: pd.DataFrame,
    i: int,
    body_mult: float = ZONE_BODY_MULTIPLIER,
    wick_pct_max: float = ZONE_WICK_PCT_MAX,
    avg_n: int = ZONE_AVG_N,
) -> bool:
    """
    Level 1 – Momentum Zone:
    - Body > body_mult * average body
    - Wick < wick_pct_max * body (total wick as fraction of body)
    """
    if i >= len(df):
        return False
    row = df.iloc[i]
    body = _body_size(row)
    if body <= 0:
        return False
    avg_b = _body_avg(df, avg_n).iloc[i]
    if avg_b <= 0:
        avg_b = body
    if body < body_mult * avg_b:
        return False
    wick_upper = _wick_upper(row)
    wick_lower = _wick_lower(row)
    wick_total = wick_upper + wick_lower
    if wick_total > wick_pct_max * body:
        return False
    return True


def _atr_or_range(df: pd.DataFrame, index: int, window: int = ATR_WINDOW) -> float:
    """Volatility threshold: rolling range (high-low) over window, or single bar range."""
    df = _normalize_columns(df)  # Ensure uppercase column names
    if index < 0 or index >= len(df):
        return 0.0
    start = max(0, index - window + 1)
    window_df = df.iloc[start : index + 1]
    if len(window_df) == 0:
        return 0.0
    rng = (window_df["High"] - window_df["Low"]).max()
    return float(rng) if pd.notna(rng) else 0.0


def is_not_fully_retraced(
    df: pd.DataFrame,
    index: int,
    zone_low: float,
    zone_high: float,
    direction_up: bool,
    lookahead: int = LOOKAHEAD_BARS,
    vol_factor: float = RETRACE_VOLATILITY_FACTOR,
) -> bool:
    """
    Adaptive retracement check using volatility (ATR / recent range).
    Returns True if the break has NOT been fully retraced (zone still valid).
    If a future bar's close comes within volatility_threshold of the zone start, consider retraced.
    """
    df = _normalize_columns(df)  # Ensure uppercase column names
    if index + lookahead >= len(df):
        return True
    volatility_threshold = _atr_or_range(df, index, ATR_WINDOW) * vol_factor
    if volatility_threshold <= 0:
        volatility_threshold = (df["High"].iloc[index] - df["Low"].iloc[index]) * vol_factor
    for j in range(1, lookahead + 1):
        if index + j >= len(df):
            break
        future = df.iloc[index + j]
        if direction_up:
            if abs(future["Close"] - zone_low) < volatility_threshold:
                return False
        else:
            if abs(future["Close"] - zone_high) < volatility_threshold:
                return False
    return True


def is_level2_zone_up(
    df: pd.DataFrame,
    i: int,
    body_mult: float = ZONE_BODY_MULTIPLIER,
    wick_pct_max: float = ZONE_WICK_PCT_MAX,
    avg_n: int = ZONE_AVG_N,
    lookahead: int = LOOKAHEAD_BARS,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> bool:
    """
    Level 2 – Structural Break Zone (up):
    - Satisfies Level 1
    - Close beyond last confirmed swing high
    - Break not fully retraced (volatility-adaptive lookahead)
    """
    df = _normalize_columns(df)  # Ensure uppercase column names
    if not is_level1_zone(df, i, body_mult, wick_pct_max, avg_n):
        return False
    swing_high = get_last_confirmed_swing_high(df, i, swing_highs=swing_highs)
    if swing_high is None:
        return False
    if df["Close"].iloc[i] <= swing_high:
        return False
    candle = df.iloc[i]
    zone_low = candle["Low"]
    zone_high = float(swing_high)
    if not is_not_fully_retraced(df, i, zone_low, zone_high, direction_up=True, lookahead=lookahead):
        return False
    return True


def is_level2_zone_down(
    df: pd.DataFrame,
    i: int,
    body_mult: float = ZONE_BODY_MULTIPLIER,
    wick_pct_max: float = ZONE_WICK_PCT_MAX,
    avg_n: int = ZONE_AVG_N,
    lookahead: int = LOOKAHEAD_BARS,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> bool:
    """
    Level 2 – Structural Break Zone (down):
    - Satisfies Level 1, close below swing low, break not retraced (adaptive).
    """
    df = _normalize_columns(df)  # Ensure uppercase column names
    if not is_level1_zone(df, i, body_mult, wick_pct_max, avg_n):
        return False
    swing_low = get_last_confirmed_swing_low(df, i, swing_lows=swing_lows)
    if swing_low is None:
        return False
    if df["Close"].iloc[i] >= swing_low:
        return False
    candle = df.iloc[i]
    zone_low = float(swing_low)
    zone_high = candle["High"]
    if not is_not_fully_retraced(df, i, zone_low, zone_high, direction_up=False, lookahead=lookahead):
        return False
    return True


def zone_level_at(
    df: pd.DataFrame,
    i: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> int:
    """
    Returns 0 (no zone), 1 (Level 1 only), or 2 (Level 2).
    Pass swing_highs/swing_lows to avoid recomputing.
    """
    if is_level2_zone_up(
        df, i,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
    ) or is_level2_zone_down(
        df, i,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
    ):
        return 2
    if is_level1_zone(df, i):
        return 1
    return 0


def zone_direction_at(
    df: pd.DataFrame,
    i: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[int]:
    """+1 upside zone, -1 downside zone, None if no zone or Level 1 only."""
    if is_level2_zone_up(df, i, swing_highs=swing_highs, swing_lows=swing_lows):
        return 1
    if is_level2_zone_down(df, i, swing_highs=swing_highs, swing_lows=swing_lows):
        return -1
    if is_level1_zone(df, i):
        row = df.iloc[i]
        return 1 if row["Close"] > row["Open"] else -1
    return None
