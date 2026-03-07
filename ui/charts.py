"""
Charts for CFD Story Dashboard. Use visualization (HKT) data only.
4H: background colored by Market Stage (green=Upside, red=Downside, neutral=no color).
1H and 15M: same style. Overlays: Level 1 zone (light gray), Level 2 (stronger), 0.5/0.618, active retracement boundary.
"""
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Stage background colors (light fill)
STAGE_UP_COLOR = "rgba(0, 128, 0, 0.12)"
STAGE_DOWN_COLOR = "rgba(200, 0, 0, 0.12)"
ZONE_LEVEL1_COLOR = "rgba(150, 150, 150, 0.25)"
ZONE_LEVEL2_COLOR = "rgba(80, 80, 80, 0.4)"
FIB_0618_COLOR = "rgba(102, 126, 234, 0.6)"
FIB_0500_COLOR = "rgba(150, 150, 234, 0.5)"
BOUNDARY_COLOR = "rgba(200, 100, 0, 0.8)"


def _stage_shapes(
    index: pd.DatetimeIndex,
    stage_series: pd.Series,
) -> List[Dict[str, Any]]:
    """Build rectangular shapes for 4H background by stage. Expects index aligned to chart."""
    shapes = []
    if stage_series is None or len(stage_series) == 0:
        return shapes
    stage_vals = stage_series.reindex(index).ffill().bfill()
    i = 0
    while i < len(index):
        s = int(stage_vals.iloc[i]) if i < len(stage_vals) else 0
        j = i
        while j < len(index) and (int(stage_vals.iloc[j]) if j < len(stage_vals) else 0) == s:
            j += 1
        if s == 1:
            shapes.append(
                dict(
                    type="rect",
                    x0=index[i],
                    x1=index[j - 1] if j > i else index[i],
                    y0=0,
                    y1=1,
                    yref="paper",
                    fillcolor=STAGE_UP_COLOR,
                    line={"width": 0},
                    layer="below",
                )
            )
        elif s == -1:
            shapes.append(
                dict(
                    type="rect",
                    x0=index[i],
                    x1=index[j - 1] if j > i else index[i],
                    y0=0,
                    y1=1,
                    yref="paper",
                    fillcolor=STAGE_DOWN_COLOR,
                    line={"width": 0},
                    layer="below",
                )
            )
        i = j
    return shapes


def _stage_shapes_for_subplot(
    df: pd.DataFrame,
    stage_series: pd.Series,
    yref: str,
) -> List[Dict[str, Any]]:
    """
    One rectangle per consecutive run of same stage (not per bar) for fast rendering.
    Returns shapes with data coords for use in make_subplots.
    """
    shapes = []
    if stage_series is None or len(df) == 0:
        return shapes
    stage_vals = stage_series.reindex(df.index).ffill().bfill()
    y0 = float(df["Low"].min())
    y1 = float(df["High"].max())
    i = 0
    while i < len(df):
        s = int(stage_vals.iloc[i]) if i < len(stage_vals) else 0
        j = i
        while j < len(df) and (int(stage_vals.iloc[j]) if j < len(stage_vals) else 0) == s:
            j += 1
        if s == 1:
            shapes.append(
                dict(
                    type="rect",
                    x0=df.index[i],
                    x1=df.index[j - 1] if j > i else df.index[i],
                    y0=y0,
                    y1=y1,
                    yref=yref,
                    fillcolor=STAGE_UP_COLOR,
                    line_width=0,
                    layer="below",
                )
            )
        elif s == -1:
            shapes.append(
                dict(
                    type="rect",
                    x0=df.index[i],
                    x1=df.index[j - 1] if j > i else df.index[i],
                    y0=y0,
                    y1=y1,
                    yref=yref,
                    fillcolor=STAGE_DOWN_COLOR,
                    line_width=0,
                    layer="below",
                )
            )
        i = j
    return shapes


def _zone_overlay(
    fig: go.Figure,
    df: pd.DataFrame,
    zone_level_series: pd.Series,
    row: int,
    col: int,
) -> None:
    """Add Level 1 (light gray) and Level 2 (stronger) zone rectangles."""
    if zone_level_series is None or len(zone_level_series) == 0:
        return
    idx = df.index
    y_min = df["Low"].min()
    y_max = df["High"].max()
    for i in range(len(df)):
        z = zone_level_series.iloc[i] if i < len(zone_level_series) else 0
        if z == 0:
            continue
        color = ZONE_LEVEL2_COLOR if z == 2 else ZONE_LEVEL1_COLOR
        t0 = idx[i]
        t1 = idx[min(i + 1, len(idx) - 1)]
        fig.add_shape(
            type="rect",
            x0=t0,
            x1=t1,
            y0=y_min,
            y1=y_max,
            fillcolor=color,
            line_width=0,
            layer="below",
            row=row,
            col=col,
        )


def chart_4h(
    df_viz: pd.DataFrame,
    stage_4h: pd.Series,
    title: str = "4H Trend",
) -> go.Figure:
    """4H chart with background colored by Market Stage. df_viz = HKT converted."""
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df_viz.index,
            open=df_viz["Open"],
            high=df_viz["High"],
            low=df_viz["Low"],
            close=df_viz["Close"],
            name="4H",
        )
    )
    shapes = _stage_shapes(df_viz.index, stage_4h)
    for sh in shapes:
        fig.add_shape(sh)
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=320,
        template="plotly_white",
        xaxis={"rangebreaks": [dict(bounds=["sat", "mon"])]},
    )
    fig.update_yaxes(title_text="Price")
    return fig


def chart_1h(
    df_viz: pd.DataFrame,
    stage_1h: pd.Series,
    zone_level: Optional[pd.Series] = None,
    title: str = "1H Structure",
) -> go.Figure:
    """1H chart. Optional zone overlay."""
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df_viz.index,
            open=df_viz["Open"],
            high=df_viz["High"],
            low=df_viz["Low"],
            close=df_viz["Close"],
            name="1H",
        )
    )
    shapes = _stage_shapes(df_viz.index, stage_1h)
    for sh in shapes:
        fig.add_shape(sh)
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=320,
        template="plotly_white",
        xaxis={"rangebreaks": [dict(bounds=["sat", "mon"])]},
    )
    fig.update_yaxes(title_text="Price")
    return fig


def chart_15m(
    df_viz: pd.DataFrame,
    stage_15m: pd.Series,
    zone_level: Optional[pd.Series] = None,
    boundary_prices: Optional[List[Optional[float]]] = None,
    fib_618: Optional[List[Optional[float]]] = None,
    fib_50: Optional[List[Optional[float]]] = None,
    title: str = "15M Deployment",
) -> go.Figure:
    """15M chart with zone overlay, 0.5/0.618 lines, active retracement boundary."""
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df_viz.index,
            open=df_viz["Open"],
            high=df_viz["High"],
            low=df_viz["Low"],
            close=df_viz["Close"],
            name="15M",
        )
    )
    shapes = _stage_shapes(df_viz.index, stage_15m)
    for sh in shapes:
        fig.add_shape(sh)
    if boundary_prices and len(boundary_prices) == len(df_viz):
        valid = [(df_viz.index[i], boundary_prices[i]) for i in range(len(df_viz)) if boundary_prices[i] is not None]
        if valid:
            fig.add_trace(
                go.Scatter(
                    x=[v[0] for v in valid],
                    y=[v[1] for v in valid],
                    mode="lines",
                    line=dict(color=BOUNDARY_COLOR, width=2, dash="dot"),
                    name="Retracement boundary",
                )
            )
    if fib_618 and len(fib_618) == len(df_viz):
        valid = [(df_viz.index[i], fib_618[i]) for i in range(len(df_viz)) if fib_618[i] is not None]
        if valid:
            fig.add_trace(
                go.Scatter(
                    x=[v[0] for v in valid],
                    y=[v[1] for v in valid],
                    mode="lines",
                    line=dict(color=FIB_0618_COLOR, width=1),
                    name="0.618",
                )
            )
    if fib_50 and len(fib_50) == len(df_viz):
        valid = [(df_viz.index[i], fib_50[i]) for i in range(len(df_viz)) if fib_50[i] is not None]
        if valid:
            fig.add_trace(
                go.Scatter(
                    x=[v[0] for v in valid],
                    y=[v[1] for v in valid],
                    mode="lines",
                    line=dict(color=FIB_0500_COLOR, width=1),
                    name="0.5",
                )
            )
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=320,
        template="plotly_white",
        xaxis={"rangebreaks": [dict(bounds=["sat", "mon"])]},
    )
    fig.update_yaxes(title_text="Price")
    return fig


def build_three_panel(
    df_4h_viz: pd.DataFrame,
    df_1h_viz: pd.DataFrame,
    df_15m_viz: pd.DataFrame,
    result: Dict[str, Any],
) -> go.Figure:
    """
    Build exactly 3 panels: Row 1 = 4H Season, Row 2 = 1H Wind, Row 3 = 15M Deployment.
    All df_*_viz must be HKT (UTC+8). result from run_narrative_engine.
    
    Features:
    - Stage background coloring (green=Upside, red=Downside)
    - Y-axis on right (TradingView style)
    - Explicit y-domains and 0.14 vertical spacing to prevent overlap
    - Weekend gaps removed
    """
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("4H Season", "1H Wind", "15M Deployment"),
        row_heights=[0.35, 0.30, 0.35],
    )
    # 4H
    fig.add_trace(
        go.Candlestick(
            x=df_4h_viz.index,
            open=df_4h_viz["Open"],
            high=df_4h_viz["High"],
            low=df_4h_viz["Low"],
            close=df_4h_viz["Close"],
            name="4H",
        ),
        row=1,
        col=1,
    )
    stage_4h = result.get("stage_4h")
    for sh in _stage_shapes_for_subplot(df_4h_viz, stage_4h, "y"):
        fig.add_shape(sh, row=1, col=1)
    # 1H
    fig.add_trace(
        go.Candlestick(
            x=df_1h_viz.index,
            open=df_1h_viz["Open"],
            high=df_1h_viz["High"],
            low=df_1h_viz["Low"],
            close=df_1h_viz["Close"],
            name="1H",
        ),
        row=2,
        col=1,
    )
    stage_1h = result.get("stage_1h")
    for sh in _stage_shapes_for_subplot(df_1h_viz, stage_1h, "y2"):
        fig.add_shape(sh, row=2, col=1)
    # 15M
    fig.add_trace(
        go.Candlestick(
            x=df_15m_viz.index,
            open=df_15m_viz["Open"],
            high=df_15m_viz["High"],
            low=df_15m_viz["Low"],
            close=df_15m_viz["Close"],
            name="15M",
        ),
        row=3,
        col=1,
    )
    stage_15m = result.get("stage_15m")
    for sh in _stage_shapes_for_subplot(df_15m_viz, stage_15m, "y3"):
        fig.add_shape(sh, row=3, col=1)
    # Disable range sliders so only three clean charts show (no extra slider charts)
    fig.update_layout(
        height=1100,
        template="plotly_white",
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=60, r=80, t=90, b=60),
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        yaxis=dict(domain=[0.68, 1.0]),
        yaxis2=dict(domain=[0.34, 0.62]),
        yaxis3=dict(domain=[0.0, 0.30]),
    )
    # Remove weekend gaps and disable range sliders on all three subplots
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], rangeslider_visible=False, row=1, col=1)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], rangeslider_visible=False, row=2, col=1)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], rangeslider_visible=False, row=3, col=1)
    # Y-axis on the right for all subplots (TradingView-style)
    fig.update_yaxes(side="right", row=1, col=1)
    fig.update_yaxes(side="right", row=2, col=1)
    fig.update_yaxes(side="right", row=3, col=1)
    return fig
