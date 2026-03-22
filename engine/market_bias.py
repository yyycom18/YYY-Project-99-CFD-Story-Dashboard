from typing import Optional

import pandas as pd

from .structure import detect_swing_highs, detect_swing_lows


def _last_two_values_at_indices(df: pd.DataFrame, indices) -> Optional[list]:
    """Helper: return list of last two values from df at given integer indices (assumes indices sorted ascending)."""
    if indices is None or len(indices) < 2:
        return None
    try:
        # take last two indices
        a, b = indices[-2], indices[-1]
        # Use 'High'/'Low' columns if present (upper-case or lower-case)
        if "High" in df.columns:
            v1 = float(df.iloc[a]["High"])
            v2 = float(df.iloc[b]["High"])
        else:
            v1 = float(df.iloc[a]["high"])
            v2 = float(df.iloc[b]["high"])
        return [v1, v2]
    except Exception:
        return None


def compute_market_bias(df: pd.DataFrame, i: int, swing_highs: Optional[pd.Series] = None, swing_lows: Optional[pd.Series] = None) -> int:
    """
    Compute market bias at index i for a dataframe df.

    Rules:
    - UP Bias (+1): last 2 swing highs increasing AND last 2 swing lows increasing
    - DOWN Bias (-1): last 2 swing highs decreasing AND last 2 swing lows decreasing
    - RANGE (0): otherwise or insufficient swings

    Parameters:
    - df: DataFrame with OHLC columns (raw engine df)
    - i: integer index position in df to evaluate (0-based)
    - swing_highs: optional boolean/0-1 Series aligned with df indicating swing highs
    - swing_lows: optional boolean/0-1 Series indicating swing lows
    """
    if df is None or df.empty:
        return 0

    # compute swings if not provided
    try:
        if swing_highs is None:
            swing_highs = detect_swing_highs(df)
        if swing_lows is None:
            swing_lows = detect_swing_lows(df)
    except Exception:
        # If detection fails, log debug and return range
        print("DEBUG market_bias: swing detection failed")
        return 0

    # find integer positions of swings strictly before i
    try:
        high_pos = [idx for idx, val in enumerate(swing_highs.tolist()) if val and idx < i]
        low_pos = [idx for idx, val in enumerate(swing_lows.tolist()) if val and idx < i]
    except Exception:
        return 0

    # Need at least two highs and two lows
    if len(high_pos) < 2 or len(low_pos) < 2:
        print("DEBUG market_bias: not enough swings (highs, lows):", len(high_pos), len(low_pos))
        return 0

    # Get last two high values and last two low values
    try:
        # highs
        ha1_idx, ha2_idx = high_pos[-2], high_pos[-1]
        la1_idx, la2_idx = low_pos[-2], low_pos[-1]
        # read values with column name handling
        if "High" in df.columns:
            h1 = float(df.iloc[ha1_idx]["High"])
            h2 = float(df.iloc[ha2_idx]["High"])
        else:
            h1 = float(df.iloc[ha1_idx]["high"])
            h2 = float(df.iloc[ha2_idx]["high"])
        if "Low" in df.columns:
            l1 = float(df.iloc[la1_idx]["Low"])
            l2 = float(df.iloc[la2_idx]["Low"])
        else:
            l1 = float(df.iloc[la1_idx]["low"])
            l2 = float(df.iloc[la2_idx]["low"])
    except Exception:
        return 0

    # check increasing / decreasing conditions
    highs_increasing = h2 > h1
    highs_decreasing = h2 < h1
    lows_increasing = l2 > l1
    lows_decreasing = l2 < l1

    if highs_increasing and lows_increasing:
        return 1
    if highs_decreasing and lows_decreasing:
        return -1
    return 0  # explicit fallback

