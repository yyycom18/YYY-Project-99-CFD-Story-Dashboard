"""
Layout builder: assembles 3-panel figure from modular plot functions.
"""
from typing import Any, Dict, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .data_provider import get_visualization_data
from .plot_deployment import plot_deployment
from .plot_structure import plot_structure
from .plot_trend import plot_trend


def build_three_panel_figure(
    df_15m: pd.DataFrame,
    df_1h: Optional[pd.DataFrame] = None,
    df_4h: Optional[pd.DataFrame] = None,
    result: Optional[Dict[str, Any]] = None,
    show_trend: bool = True,
    show_blocking: bool = True,
) -> go.Figure:
    """
    Build 3-panel Plotly figure (4H, 1H, 15M).
    
    Args:
        df_15m, df_1h, df_4h: OHLC DataFrames (lowercase columns: open, high, low, close)
        result: Engine result (optional)
        show_trend, show_blocking: Toggle flags
    
    Returns:
        Plotly figure
    """
    # Create subplots
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.08,
        subplot_titles=("4H Trend", "1H Structure", "15M Deployment"),
        row_heights=[0.35, 0.35, 0.30],
    )
    
    # Get visualization data
    viz = get_visualization_data(df_15m, df_1h, df_4h, result)
    
    # Build each panel
    if df_4h is not None and not df_4h.empty:
        plot_trend(fig, df_4h, viz.get("4h", {}), row=1, col=1,
                   show_trend=show_trend, show_blocking=show_blocking)
    
    if df_1h is not None and not df_1h.empty:
        plot_structure(fig, df_1h, viz.get("1h", {}), row=2, col=1,
                       show_blocking=show_blocking)
    
    plot_deployment(fig, df_15m, viz.get("15m", {}), row=3, col=1)
    
    # Layout
    fig.update_layout(
        height=1000,
        template="plotly_white",
        showlegend=False,
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        margin=dict(l=50, r=100, t=80, b=50),
    )
    
    # Remove weekend gaps and configure axes
    for r in [1, 2, 3]:
        fig.update_xaxes(
            rangebreaks=[dict(bounds=["sat", "mon"])],
            row=r,
            col=1,
        )
        fig.update_yaxes(side="right", row=r, col=1)
    
    return fig
