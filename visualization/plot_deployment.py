"""
15M Deployment Chart: candlestick only (simplest view).
"""
from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go

from .overlays import add_candlestick


def plot_deployment(
    fig: go.Figure,
    df: pd.DataFrame,
    viz_data: Dict[str, Any],
    row: int,
    col: int,
) -> None:
    """
    Plot 15M deployment chart.
    
    Args:
        fig: Plotly figure
        df: OHLC data (columns: open, high, low, close)
        viz_data: Visualization data from data_provider
        row, col: Subplot position
    """
    if df is None or df.empty:
        return
    
    # Add candlestick
    add_candlestick(fig, df, row, col, name="15M")
