"""
Plotly overlay helper functions for clean, modular chart building.
"""
from typing import List, Optional, Tuple

import plotly.graph_objects as go


def add_candlestick(
    fig: go.Figure,
    df,
    row: int,
    col: int,
    name: str = "OHLC",
) -> None:
    """Add candlestick trace to subplot."""
    df = df.rename(columns={c: c.lower() for c in df.columns})
    
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=name,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=row,
        col=col,
    )


def add_swing_markers(
    fig: go.Figure,
    swing_highs: List[Tuple],
    swing_lows: List[Tuple],
    row: int,
    col: int,
) -> None:
    """Add swing high (triangle-up) and swing low (triangle-down) markers."""
    if swing_highs:
        x_h = [t[0] for t in swing_highs]
        y_h = [t[1] for t in swing_highs]
        fig.add_trace(
            go.Scatter(
                x=x_h,
                y=y_h,
                mode="markers",
                marker=dict(symbol="triangle-up", size=8, color="green"),
                name="Swing High",
                showlegend=False,
            ),
            row=row,
            col=col,
        )
    
    if swing_lows:
        x_l = [t[0] for t in swing_lows]
        y_l = [t[1] for t in swing_lows]
        fig.add_trace(
            go.Scatter(
                x=x_l,
                y=y_l,
                mode="markers",
                marker=dict(symbol="triangle-down", size=8, color="red"),
                name="Swing Low",
                showlegend=False,
            ),
            row=row,
            col=col,
        )


def add_blocking_levels(
    fig: go.Figure,
    blocking_highs: List[float],
    blocking_lows: List[float],
    x_min,
    x_max,
    row: int,
    col: int,
) -> None:
    """Add blocking level lines (horizontal)."""
    for price in blocking_highs[:2]:  # Top 2
        fig.add_hline(
            y=price,
            line_dash="dash",
            line_color="black",
            opacity=0.5,
            row=row,
            col=col,
        )
    
    for price in blocking_lows[:2]:  # Bottom 2
        fig.add_hline(
            y=price,
            line_dash="dash",
            line_color="black",
            opacity=0.5,
            row=row,
            col=col,
        )


def add_zone_rect(
    fig: go.Figure,
    t0,
    t1,
    z_low: float,
    z_high: float,
    row: int,
    col: int,
    zone_type: str = "demand",
    opacity: float = 0.2,
) -> None:
    """Add zone rectangle (demand or supply)."""
    color = "orange" if zone_type == "demand" else "gray"
    
    fig.add_shape(
        type="rect",
        x0=t0,
        x1=t1,
        y0=z_low,
        y1=z_high,
        fillcolor=color,
        line_width=0,
        opacity=opacity,
        layer="below",
        row=row,
        col=col,
    )
