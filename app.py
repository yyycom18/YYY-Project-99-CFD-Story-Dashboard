"""
CFD Story Dashboard — Narrative Story Monitor.
Shows where the market story stands across 4H Season, 1H Wind, 15M Deployment.
Real market data via yfinance. Raw data → engine only. All visualization uses HKT (UTC+8) via convert_to_HKT().
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from data.market_data import fetch_all_timeframes, SYMBOL_MAP
from engine.narrative import run_narrative_engine
from visualization.layout import build_three_panel_figure
from ui.table import build_opportunity_rows, render_opportunity_table
from utils.timezone import convert_to_HKT, timestamp_to_HKT_display

st.set_page_config(
    page_title="CFD Story Dashboard",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=300)
def _cached_fetch_and_run(asset: str, lookback_days: int):
    """Fetch real market data and run narrative engine. Cached for 5 min."""
    data_raw = fetch_all_timeframes(asset, lookback_days=lookback_days)
    if not data_raw or "15M" not in data_raw:
        return None, None, None, None
    df_4h_raw = data_raw["4H"]
    df_1h_raw = data_raw["1H"]
    df_15m_raw = data_raw["15M"]
    result = run_narrative_engine(df_4h_raw, df_1h_raw, df_15m_raw, asset)
    return df_4h_raw, df_1h_raw, df_15m_raw, result


st.title("CFD Story Dashboard")
st.caption("Narrative Story Monitor — Real market data via yfinance. 4H Season → 1H Wind → 15M Deployment")

# Sidebar configuration
asset = st.sidebar.selectbox("Asset", list(SYMBOL_MAP.keys()), index=0)

# Lookback days: chart display and engine history
lookback_days = st.sidebar.slider("Lookback Days", 5, 30, 15, 1,
    help="Fetch last N days of 15M data for engine and display")

with st.spinner("Loading real market data and running narrative engine… (~10–20s first time, instant on cache)"):
    df_4h_raw, df_1h_raw, df_15m_raw, result = _cached_fetch_and_run(asset, lookback_days)

if df_4h_raw is None or df_15m_raw is None:
    st.warning(f"No data available for {asset}. Try a different asset or reduce lookback days.")
    st.stop()

# ----- Engine result -----
if result is None:
    st.error("Narrative engine returned None.")
    st.stop()

with st.expander("Data & engine info", expanded=False):
    st.write("Data sizes (bars):", {"4H": len(df_4h_raw), "1H": len(df_1h_raw), "15M": len(df_15m_raw)})
    st.write("Engine result keys:", list(result.keys()))

# ----- Narrative Summary Panel -----
_STAGE_LABELS = {-1: "Downside", 0: "Neutral", 1: "Upside"}
_NARRATIVE_LABELS = {0: "Env", 1: "Trend/Shift", 2: "Retracement", 3: "Deployment", 4: "Liquidity", 5: "Resolution"}


def _last_scalar(x, default="-"):
    """Get last value from series or list for display."""
    if x is None:
        return default
    if hasattr(x, "iloc"):
        return x.iloc[-1] if len(x) else default
    if isinstance(x, list):
        return x[-1] if len(x) else default
    return x


s4h = result.get("stage_4h")
s1h = result.get("stage_1h")
ns = result.get("narrative_stage")
zl = result.get("zone_level")
bt = result.get("boundary_type")
rr_list = result.get("rr")
dt_list = result.get("deployment_trigger")

v4 = _last_scalar(s4h)
v1 = _last_scalar(s1h)
vn = _last_scalar(ns)
vzl = _last_scalar(zl)
vbt = _last_scalar(bt)
vrr = _last_scalar(rr_list)
vdt = _last_scalar(dt_list)

st.subheader("Current Narrative State")
st.caption("Story position: 4H Season → 1H Wind → Narrative Stage (Primary) | Zone & Deployment Details (Secondary)")

# Primary: 4H Season, 1H Wind, Narrative Stage
primary_cols = st.columns(3)
with primary_cols[0]:
    season_val = _STAGE_LABELS.get(int(v4), str(v4)) if v4 != "-" else v4
    st.metric("🔵 4H Season", season_val, help="Higher timeframe trend direction (Upside/Neutral/Downside)")
with primary_cols[1]:
    wind_val = _STAGE_LABELS.get(int(v1), str(v1)) if v1 != "-" else v1
    st.metric("💨 1H Wind", wind_val, help="Current structure within the season")
with primary_cols[2]:
    stage_val = _NARRATIVE_LABELS.get(int(vn), str(vn)) if vn != "-" else vn
    st.metric("📖 Narrative Stage", stage_val, help="Story position (0=Env → 5=Resolution)")

# Secondary: Zone Level, Boundary Type, R:R, Deployment Trigger
with st.expander("🔎 Details: Zone Level, Boundary Type, R:R, Deployment", expanded=False):
    sec_cols = st.columns(4)
    with sec_cols[0]:
        zone_val = str(int(vzl)) if isinstance(vzl, (int, float)) else vzl
        st.metric("Zone Level", zone_val, help="1 = Momentum | 2 = Structural Break")
    with sec_cols[1]:
        st.metric("Boundary Type", str(vbt) if vbt != "-" else vbt, help="0.618 or Zone-Dominant")
    with sec_cols[2]:
        rr_display = f"{float(vrr):.2f}" if isinstance(vrr, (int, float)) else (vrr if vrr != "-" else "-")
        st.metric("R:R", rr_display, help="Risk:Reward ratio for deployment (min 1:1.3)")
    with sec_cols[3]:
        dt_display = "Yes ✓" if vdt is True else ("No" if vdt is False else str(vdt))
        st.metric("Deployment Trigger", dt_display, help="Ready to deploy?")

st.markdown("---")

# ----- Weekly Opportunity Table -----
st.subheader("Weekly Opportunity Log – Last 4 Weeks")
try:
    rows = build_opportunity_rows(result, df_15m_raw, lookback_weeks=4)
    render_opportunity_table(rows)
except Exception as e:
    st.error("Opportunity table failed to render.")
    st.exception(e)
st.markdown("---")

# ----- Three-panel chart: Real market data (HKT viz) -----
st.subheader(f"{asset} – 4H Season / 1H Wind / 15M Deployment")

# Convert to HKT for visualization only
df_4h_viz = convert_to_HKT(df_4h_raw)
df_1h_viz = convert_to_HKT(df_1h_raw)
df_15m_viz = convert_to_HKT(df_15m_raw)

try:
    fig = build_three_panel_figure(df_15m_viz, df_1h_viz, df_4h_viz, result)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error("Chart rendering failed.")
    st.exception(e)

st.sidebar.markdown("---")
st.sidebar.info("📊 Real market data via yfinance (15M → 1H/4H auto-resample). Cached for fast subsequent loads.")
