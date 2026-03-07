"""
1H Structure Chart: candlestick + blocking levels.
"""
from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go

from .overlays import (
    add_blocking_levels,
    add_candlestick,
)


def plot_structure(
    fig: go.Figure,
    df: pd.DataFrame,
    viz_data: Dict[str, Any],
    row: int,
    col: int,
    show_blocking: bool = True,
) -> None:
    """
    Plot 1H structure chart.
    
    Args:
        fig: Plotly figure
        df: OHLC data (columns: open, high, low, close)
        viz_data: Visualization data from data_provider
        row, col: Subplot position
        show_blocking: Show blocking levels
    """
    if df is None or df.empty:
        return
    
    # Add candlestick
    add_candlestick(fig, df, row, col, name="1H")
    
    if not viz_data:
        return
    
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
