"""
4H Trend Chart: candlestick + swing markers + blocking levels.
"""
from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go

from .overlays import (
    add_blocking_levels,
    add_candlestick,
    add_swing_markers,
)


def plot_trend(
    fig: go.Figure,
    df: pd.DataFrame,
    viz_data: Dict[str, Any],
    row: int,
    col: int,
    show_trend: bool = True,
    show_blocking: bool = True,
) -> None:
    """
    Plot 4H trend chart.
    
    Args:
        fig: Plotly figure
        df: OHLC data (columns: open, high, low, close)
        viz_data: Visualization data from data_provider
        row, col: Subplot position
        show_trend: Show swing high/low markers
        show_blocking: Show blocking levels
    """
    if df is None or df.empty:
        return
    
    # Add candlestick
    add_candlestick(fig, df, row, col, name="4H")
    
    if not viz_data:
        return
    
    # Add swing markers (visual only) when requested
    if show_trend:
        add_swing_markers(
            fig,
            viz_data.get("swing_highs", []),
            viz_data.get("swing_lows", []),
            row,
            col,
        )
    
    # Add blocking levels
    if show_blocking:
        x_min, x_max = df.index[0], df.index[-1]
        add_blocking_levels(
            fig,
            viz_data.get("blocking_highs", [])[:2],
            viz_data.get("blocking_lows", [])[:2],
            x_min,
            x_max,
            row,
            col,
        )
