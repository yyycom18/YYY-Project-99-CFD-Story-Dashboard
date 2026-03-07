"""
Fib interaction: 0.618 default retracement boundary.
Zone-Dominant: if Level 2 zone exists, boundary = zone start (no 0.5–0.618 range lock).
Zone can be 0.45, 0.5, 0.7, etc. – zone truly overrides 0.618.
Engine uses raw UTC data only.
"""
from typing import Optional, Tuple

import pandas as pd

from .structure import get_last_confirmed_swing_high, get_last_confirmed_swing_low, _normalize_columns
from .zone import is_level2_zone_up, is_level2_zone_down

FIB_DEFAULT = 0.618


def _range_high_low(
    df: pd.DataFrame,
    up_to_idx: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[Tuple[float, float]]:
    """(swing_high, swing_low) of the last completed swing structure before up_to_idx."""
    sh = get_last_confirmed_swing_high(df, up_to_idx, swing_highs=swing_highs)
    sl = get_last_confirmed_swing_low(df, up_to_idx, swing_lows=swing_lows)
    if sh is None or sl is None:
        return None
    return (sh, sl)


def retracement_levels(
    df: pd.DataFrame,
    i: int,
    direction: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[Tuple[float, float, float]]:
    """
    For bar i, get (low, high, range) of the move being retraced.
    direction +1 = bull move (retrace from high), -1 = bear move (retrace from low).
    Returns (start, end, range_size).
    """
    rng = _range_high_low(df, i, swing_highs=swing_highs, swing_lows=swing_lows)
    if rng is None:
        return None
    sh, sl = rng
    size = sh - sl
    if size <= 0:
        return None
    if direction == 1:
        return (sl, sh, size)
    return (sh, sl, -size)


def default_boundary_price(
    df: pd.DataFrame,
    i: int,
    direction: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[float]:
    """
    0.618 retracement price. direction +1 = bull (boundary from high), -1 = bear (from low).
    """
    levels = retracement_levels(
        df, i, direction,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
    )
    if levels is None:
        return None
    start, end, size = levels
    if direction == 1:
        return end - FIB_DEFAULT * (end - start)
    return start + FIB_DEFAULT * (start - end)


def zone_dominant_boundary_price(
    df: pd.DataFrame,
    i: int,
    direction: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[float]:
    """
    Zone-Dominant: if Level 2 zone exists, return zone start as boundary (no fib range lock).
    Zone can be at 0.45, 0.5, 0.618, 0.7, etc. – zone start overrides 0.618 whenever L2 zone exists.
    """
    df = _normalize_columns(df)  # Ensure uppercase column names
    for j in range(max(0, i - 10), i + 1):
        if j >= len(df):
            break
        if direction == 1:
            if is_level2_zone_up(
                df, j,
                swing_highs=swing_highs,
                swing_lows=swing_lows,
            ):
                return float(df["Low"].iloc[j])
        else:
            if is_level2_zone_down(
                df, j,
                swing_highs=swing_highs,
                swing_lows=swing_lows,
            ):
                return float(df["High"].iloc[j])
    return None


def compute_boundary(
    default_618: Optional[float],
    zone_level: int,
    zone_start: Optional[float],
) -> Optional[float]:
    """
    If Level 2 zone exists and zone_start is not None: return zone_start.
    Else: return default_618.
    """
    if zone_level == 2 and zone_start is not None:
        return zone_start
    return default_618


def active_retracement_boundary(
    df: pd.DataFrame,
    i: int,
    direction: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Tuple[Optional[float], str]:
    """
    Returns (boundary_price, boundary_type).
    boundary_type = "0.618" or "Zone-Dominant".
    Zone-Dominant whenever Level 2 zone exists (no 0.5–0.618 restriction).
    """
    zone_start = zone_dominant_boundary_price(
        df, i, direction,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
    )
    default = default_boundary_price(
        df, i, direction,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
    )
    zone_level = 2 if zone_start is not None else 0
    boundary = compute_boundary(default, zone_level, zone_start)
    if boundary is not None and zone_start is not None and boundary == zone_start:
        return (boundary, "Zone-Dominant")
    return (default, "0.618")
