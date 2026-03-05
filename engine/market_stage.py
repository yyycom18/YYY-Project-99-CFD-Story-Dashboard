"""
Market Stage per TF: +1 Upside, 0 Neutral, -1 Downside.

4H = 季節 (season): structure break defines season shift.
1H = 風向 (wind): only flip direction if retracement > 0.68; otherwise inherit parent (4H) stage.
Engine uses raw UTC data only.
"""
from typing import Optional

import pandas as pd
import numpy as np

from .structure import (
    detect_swing_highs,
    detect_swing_lows,
    is_structure_break_up,
    is_structure_break_down,
    get_last_confirmed_swing_high,
    get_last_confirmed_swing_low,
)

# 1H: must exceed this retracement ratio to allow direction flip from parent
RETRACE_THRESHOLD_1H = 0.68


def _structure_break_at(
    df: pd.DataFrame,
    i: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[str]:
    """Return "UP", "DOWN", or None at bar i. Pass swing_highs/swing_lows to avoid recomputing."""
    if i >= len(df) or i < 0:
        return None
    if is_structure_break_up(df, i, swing_highs=swing_highs):
        return "UP"
    if is_structure_break_down(df, i, swing_lows=swing_lows):
        return "DOWN"
    return None


def _retracement_ratio_at(
    df: pd.DataFrame,
    i: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[float]:
    """
    Retracement depth from last swing high (bull) or low (bear).
    Returns ratio in [0, 1]: 0 = no retracement, 1 = full retracement.
    Uses current bar low vs swing high for bull move; current bar high vs swing low for bear.
    """
    if i >= len(df) or i < 0:
        return None
    sh = get_last_confirmed_swing_high(df, i, swing_highs=swing_highs)
    sl = get_last_confirmed_swing_low(df, i, swing_lows=swing_lows)
    if sh is None or sl is None or sh <= sl:
        return None
    row = df.iloc[i]
    # Bull retrace: from high downwards. Ratio = (swing_high - current_low) / range
    bull_retrace = (sh - row["Low"]) / (sh - sl)
    # Bear retrace: from low upwards. Ratio = (current_high - swing_low) / range
    bear_retrace = (row["High"] - sl) / (sh - sl)
    # Use the one that indicates deeper retracement (max)
    r = max(0.0, min(1.0, max(bull_retrace, bear_retrace)))
    return r


def compute_market_stage(
    structure_break: Optional[str],
    retracement_ratio: Optional[float] = None,
    parent_stage: Optional[int] = None,
) -> int:
    """
    Market Stage Logic.

    4H (parent_stage is None):
        Structure break defines season shift. UP -> 1, DOWN -> -1, else 0.

    1H (parent_stage is not None):
        Only flip direction if retracement_ratio > 0.68.
        Otherwise inherit parent (4H) stage bias.
    """
    if parent_stage is None:
        # 4H logic – season
        if structure_break == "UP":
            return 1
        if structure_break == "DOWN":
            return -1
        return 0

    # 1H logic – wind; do not flip unless retracement > 0.68
    # CRITICAL: retracement_ratio can be None when swing not yet formed – must not flip.
    if retracement_ratio is None:
        return parent_stage if parent_stage is not None else 0
    if retracement_ratio > RETRACE_THRESHOLD_1H:
        if structure_break == "DOWN":
            return -1
        if structure_break == "UP":
            return 1

    # Otherwise inherit higher timeframe
    return parent_stage if parent_stage is not None else 0


def market_stage_at_4h(
    df: pd.DataFrame,
    i: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> int:
    """4H stage (season): structure break only."""
    if i >= len(df) or i < 0:
        return 0
    sb = _structure_break_at(df, i, swing_highs=swing_highs, swing_lows=swing_lows)
    return compute_market_stage(sb, parent_stage=None)


def market_stage_at_1h(
    df: pd.DataFrame,
    i: int,
    parent_stage: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> int:
    """1H stage (wind): flip only if retracement > 0.68, else inherit parent."""
    if i >= len(df) or i < 0:
        return parent_stage
    sb = _structure_break_at(df, i, swing_highs=swing_highs, swing_lows=swing_lows)
    rr = _retracement_ratio_at(df, i, swing_highs=swing_highs, swing_lows=swing_lows)
    return compute_market_stage(sb, retracement_ratio=rr, parent_stage=parent_stage)


def market_stage_at(
    df: pd.DataFrame,
    i: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> int:
    """
    Returns +1 (Upside), 0 (Neutral), or -1 (Downside).
    Used for 15M or when no parent (standalone). Keeps original structure+sequence logic.
    """
    if i >= len(df) or i < 0:
        return 0
    sb = _structure_break_at(df, i, swing_highs=swing_highs, swing_lows=swing_lows)
    return compute_market_stage(sb, parent_stage=None)


def market_stage_series(
    df: pd.DataFrame,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> pd.Series:
    """4H-style stage series (structure break only). Precomputes swing once if not provided."""
    if swing_highs is None:
        swing_highs = detect_swing_highs(df)
    if swing_lows is None:
        swing_lows = detect_swing_lows(df)
    stages = []
    for i in range(len(df)):
        stages.append(
            market_stage_at_4h(df, i, swing_highs=swing_highs, swing_lows=swing_lows)
        )
    return pd.Series(stages, index=df.index)


def market_stage_series_1h_with_parent(
    df_1h: pd.DataFrame,
    parent_stage_series: pd.Series,
    index_1h: pd.DatetimeIndex,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> pd.Series:
    """1H stage series with parent (4H) alignment by timestamp. Precomputes swing once if not provided."""
    if swing_highs is None:
        swing_highs = detect_swing_highs(df_1h)
    if swing_lows is None:
        swing_lows = detect_swing_lows(df_1h)
    parent_aligned = parent_stage_series.reindex(index_1h, method="ffill")
    stages = []
    for i in range(len(df_1h)):
        p = int(parent_aligned.iloc[i]) if i < len(parent_aligned) and pd.notna(parent_aligned.iloc[i]) else 0
        stages.append(
            market_stage_at_1h(
                df_1h, i, p,
                swing_highs=swing_highs,
                swing_lows=swing_lows,
            )
        )
    return pd.Series(stages, index=df_1h.index)
