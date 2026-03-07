"""
Narrative Coach Engine v1 – Story State Machine.
Stages: 0 Environment, 1 Trend Continuation OR Structure Shift, 2 Retracement, 3 Deployment Window, 4 Liquidity Event, 5 Resolution.
Engine uses raw UTC data only. No timezone conversion.
"""
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .market_stage import (
    market_stage_at,
    market_stage_at_1h,
    market_stage_at_4h,
    market_stage_series,
    market_stage_series_1h_with_parent,
)
from .zone import zone_level_at
from .structure import (
    detect_swing_highs,
    detect_swing_lows,
    get_last_confirmed_swing_high,
    get_last_confirmed_swing_low,
    _normalize_columns,
)
from .fib_logic import active_retracement_boundary

MIN_RR = 1.0
MIN_RR_REWARD = 1.3


def narrative_stage_at(
    df_4h: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_15m: pd.DataFrame,
    i_4h: int,
    i_1h: int,
    i_15m: int,
) -> int:
    """
    Returns narrative stage 0–5 (story position). Independent of RR – RR is display only.
    Stage = current story position descriptor, not an entry filter.
    """
    if i_4h >= len(df_4h) or i_1h >= len(df_1h) or i_15m >= len(df_15m):
        return 0
    stage_4h = market_stage_at_4h(df_4h, i_4h)
    stage_1h = market_stage_at_1h(df_1h, i_1h, stage_4h)
    z = zone_level_at(df_15m, i_15m)
    if stage_4h == 0 and stage_1h == 0:
        return 0
    if z >= 2:
        return 2
    if stage_4h != 0 and stage_1h != 0 and (stage_4h == stage_1h or stage_1h != 0):
        return 3
    return 1


def _narrative_stage_from_aligned(stage_4h: int, stage_1h: int, zone_level: int) -> int:
    """Narrative stage from precomputed 4H/1H stage and zone level (avoids recomputing)."""
    if stage_4h == 0 and stage_1h == 0:
        return 0
    if zone_level >= 2:
        return 2
    if stage_4h != 0 and stage_1h != 0 and (stage_4h == stage_1h or stage_1h != 0):
        return 3
    return 1


def compute_rr(
    entry: Optional[float],
    stop: Optional[float],
    target: Optional[float],
) -> Optional[float]:
    """
    R:R = reward / risk.
    risk = abs(entry - stop), reward = abs(target - entry).
    CRITICAL: Returns None if entry/stop/target is None (e.g. swing not formed) to avoid polluting weekly review with 0 RR.
    """
    if entry is None or stop is None or target is None:
        return None
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk == 0:
        return None
    return reward / risk


def _rr_at_bar(
    df: pd.DataFrame,
    i: int,
    direction: int,
    boundary_price: float,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Optional[float]:
    """
    R:R using real stop (structure invalid level = boundary) and target (liquidity level = swing).
    entry = close, stop = boundary, target = swing high (long) or swing low (short).
    CRITICAL: Returns None when target is None (swing not formed) – never return 0 to avoid polluting weekly review.
    """
    row = df.iloc[i]
    entry = float(row["Close"])
    stop = float(boundary_price)
    if direction == 1:
        target = get_last_confirmed_swing_high(df, i, swing_highs=swing_highs)
        if target is None or entry >= target or entry <= stop:
            return None
        target = float(target)
    else:
        target = get_last_confirmed_swing_low(df, i, swing_lows=swing_lows)
        if target is None or entry <= target or entry >= stop:
            return None
        target = float(target)
    return compute_rr(entry, stop, target)


def deployment_trigger_valid(
    df_4h: pd.DataFrame,
    df_15m: pd.DataFrame,
    i_4h: int,
    i_15m: int,
    stage_4h: int,
    stage_1h: int,
    boundary_price: Optional[float],
    boundary_type: str,
    direction: int,
    swing_highs: Optional[pd.Series] = None,
    swing_lows: Optional[pd.Series] = None,
) -> Tuple[bool, Optional[float]]:
    """
    Deployment requires: alignment with 4H narrative OR counter-trend with R:R >= 1:1.3;
    and occurs inside retracement boundary.
    Returns (valid, rr_ratio).
    """
    if boundary_price is None or i_15m >= len(df_15m):
        return (False, None)
    rr = _rr_at_bar(
        df_15m, i_15m, direction, boundary_price,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
    )
    if rr is None or rr < MIN_RR_REWARD:
        return (False, rr)
    aligned = (stage_4h == direction) or (stage_4h != 0 and stage_1h == direction)
    counter_ok = (stage_4h != direction) and (rr >= MIN_RR_REWARD)
    if not aligned and not counter_ok:
        return (False, rr)
    return (True, rr)


def run_narrative_engine(
    df_4h: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_15m: pd.DataFrame,
    asset: str,
) -> Dict[str, Any]:
    """
    Run narrative engine on raw UTC data. Returns state per bar and opportunity log.
    df_* are raw; do not pass viz-converted data.
    Normalizes column names internally to handle both lowercase (yfinance) and uppercase formats.
    """
    # Normalize all dataframes to uppercase column names (engine expects this)
    df_4h = _normalize_columns(df_4h)
    df_1h = _normalize_columns(df_1h)
    df_15m = _normalize_columns(df_15m)
    
    n_15 = len(df_15m)
    if n_15 == 0:
        return {
            "asset": asset,
            "stage_4h": pd.Series(dtype=int),
            "stage_1h": pd.Series(dtype=int),
            "stage_15m": pd.Series(dtype=int),
            "zone_level": pd.Series(dtype=int),
            "boundary_type": [],
            "boundary_price": [],
            "rr": [],
            "deployment_trigger": [],
            "narrative_stage": [],
            "stage_4h_aligned": [],
            "stage_1h_aligned": [],
            "opportunities": [],
        }

    # Precompute swing series once per dataframe (avoids O(n²) repeated detection)
    swing_highs_4h = detect_swing_highs(df_4h)
    swing_lows_4h = detect_swing_lows(df_4h)
    swing_highs_1h = detect_swing_highs(df_1h)
    swing_lows_1h = detect_swing_lows(df_1h)
    swing_highs_15 = detect_swing_highs(df_15m)
    swing_lows_15 = detect_swing_lows(df_15m)

    stage_4h_s = market_stage_series(
        df_4h,
        swing_highs=swing_highs_4h,
        swing_lows=swing_lows_4h,
    )
    stage_1h_s = market_stage_series_1h_with_parent(
        df_1h, stage_4h_s, df_1h.index,
        swing_highs=swing_highs_1h,
        swing_lows=swing_lows_1h,
    )
    stage_15m_s = market_stage_series(
        df_15m,
        swing_highs=swing_highs_15,
        swing_lows=swing_lows_15,
    )

    # Align 15m bar index to 4H/1H bar indices by timestamp
    idx_15 = df_15m.index
    i_4h_map = df_4h.index.get_indexer(idx_15, method="ffill")
    i_1h_map = df_1h.index.get_indexer(idx_15, method="ffill")

    boundary_types: List[str] = []
    boundary_prices: List[Optional[float]] = []
    rrs: List[Optional[float]] = []
    deployment_triggers: List[bool] = []
    narrative_stages: List[int] = []
    stage_4h_aligned: List[int] = []
    stage_1h_aligned: List[int] = []
    zone_levels: List[int] = []

    for i in range(n_15):
        i_4h = int(i_4h_map[i]) if i_4h_map[i] >= 0 else 0
        i_1h = int(i_1h_map[i]) if i_1h_map[i] >= 0 else 0
        st_4h = int(stage_4h_s.iloc[i_4h]) if i_4h < len(stage_4h_s) else 0
        st_1h = int(stage_1h_s.iloc[i_1h]) if i_1h < len(stage_1h_s) else 0
        stage_4h_aligned.append(st_4h)
        stage_1h_aligned.append(st_1h)
        st_15 = int(stage_15m_s.iloc[i])
        direction = 1 if st_15 == 1 else (-1 if st_15 == -1 else 0)

        z = zone_level_at(
            df_15m, i,
            swing_highs=swing_highs_15,
            swing_lows=swing_lows_15,
        )
        zone_levels.append(z)

        boundary_price, btype = (
            active_retracement_boundary(
                df_15m, i, direction,
                swing_highs=swing_highs_15,
                swing_lows=swing_lows_15,
            )
            if direction != 0
            else (None, "0.618")
        )
        boundary_types.append(btype)
        boundary_prices.append(boundary_price)
        rr = (
            _rr_at_bar(
                df_15m, i, direction, boundary_price,
                swing_highs=swing_highs_15,
                swing_lows=swing_lows_15,
            )
            if boundary_price is not None and direction != 0
            else None
        )
        rrs.append(rr)
        valid, _ = (
            deployment_trigger_valid(
                df_4h, df_15m, i_4h, i, st_4h, st_1h, boundary_price, btype, direction,
                swing_highs=swing_highs_15,
                swing_lows=swing_lows_15,
            )
            if boundary_price is not None and direction != 0 and rr is not None and rr >= MIN_RR_REWARD
            else (False, None)
        )
        deployment_triggers.append(valid)
        narrative_stages.append(_narrative_stage_from_aligned(st_4h, st_1h, z))
    opportunities: List[Dict[str, Any]] = []
    return {
        "asset": asset,
        "stage_4h": stage_4h_s,
        "stage_1h": stage_1h_s,
        "stage_15m": pd.Series(stage_15m_s.values, index=df_15m.index),
        "zone_level": pd.Series(zone_levels, index=df_15m.index),
        "boundary_type": boundary_types,
        "boundary_price": boundary_prices,
        "rr": rrs,
        "deployment_trigger": deployment_triggers,
        "narrative_stage": narrative_stages,
        "stage_4h_aligned": stage_4h_aligned,
        "stage_1h_aligned": stage_1h_aligned,
        "opportunities": opportunities,
    }
