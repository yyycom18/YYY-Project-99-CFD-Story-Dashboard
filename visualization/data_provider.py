"""
Visualization data provider: computes overlay coordinates from OHLC data.
Does not modify scores. Only provides visualization data.
"""
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from engine.structure import (
    detect_swing_highs,
    detect_swing_lows,
)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure columns are lowercase: open, high, low, close."""
    if df is None or df.empty:
        return df
    m = {c: c.lower() for c in df.columns if c.lower() in ("open", "high", "low", "close")}
    return df.rename(columns=m) if m else df


def get_swing_points(df: pd.DataFrame) -> Tuple[List[Tuple[Any, float]], List[Tuple[Any, float]]]:
    """
    Return swing high/low markers as (time, price) tuples.
    """
    df = _normalize_columns(df)
    if df is None or len(df) < 5:
        return [], []
    
    swing_highs_bool = detect_swing_highs(df)
    swing_lows_bool = detect_swing_lows(df)
    
    # Convert boolean series to list of indices where True
    swing_highs_idx = [i for i, v in enumerate(swing_highs_bool) if v]
    swing_lows_idx = [i for i, v in enumerate(swing_lows_bool) if v]
    
    idx = df.index
    highs = [(idx[i], float(df["high"].iloc[i])) for i in swing_highs_idx]
    lows = [(idx[i], float(df["low"].iloc[i])) for i in swing_lows_idx]
    
    return highs, lows


def get_blocking_levels(df: pd.DataFrame) -> Tuple[List[float], List[float]]:
    """Return top 2 swing high and low levels for blocking lines."""
    df = _normalize_columns(df)
    if df is None or len(df) < 5:
        return [], []
    
    swing_highs_bool = detect_swing_highs(df)
    swing_lows_bool = detect_swing_lows(df)
    
    # Convert boolean series to list of indices where True
    swing_highs_idx = [i for i, v in enumerate(swing_highs_bool) if v]
    swing_lows_idx = [i for i, v in enumerate(swing_lows_bool) if v]
    
    h_vals = sorted([float(df["high"].iloc[i]) for i in swing_highs_idx], reverse=True)[:2]
    l_vals = sorted([float(df["low"].iloc[i]) for i in swing_lows_idx])[:2]
    
    return h_vals, l_vals


def get_visualization_data(
    df_15m: pd.DataFrame,
    df_1h: Optional[pd.DataFrame] = None,
    df_4h: Optional[pd.DataFrame] = None,
    result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build overlay coordinates for visualization layer.
    Does NOT modify scores or engine logic.
    
    Returns:
        {
            "4h": {"swing_highs": [...], "swing_lows": [...], ...},
            "1h": {...},
            "15m": {...},
        }
    """
    out = {
        "4h": {"swing_highs": [], "swing_lows": [], "blocking_highs": [], "blocking_lows": []},
        "1h": {"swing_highs": [], "swing_lows": [], "blocking_highs": [], "blocking_lows": []},
        "15m": {"swing_highs": [], "swing_lows": [], "blocking_highs": [], "blocking_lows": []},
    }
    
    for label, df in [("4h", df_4h), ("1h", df_1h), ("15m", df_15m)]:
        if df is None or len(df) < 5:
            continue
        
        df = _normalize_columns(df)
        highs, lows = get_swing_points(df)
        h_vals, l_vals = get_blocking_levels(df)
        
        out[label]["swing_highs"] = highs
        out[label]["swing_lows"] = lows
        out[label]["blocking_highs"] = h_vals
        out[label]["blocking_lows"] = l_vals
    
    return out
