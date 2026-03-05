"""
CFD Story Dashboard — Narrative Coach Engine v1.
NOT a scoring dashboard. Narrative state reflects structural market flow.
Raw data → engine only. Visualization uses HKT-converted copy.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import streamlit as st

from data.fetch import ASSETS, fetch_all_timeframes
from engine.narrative import run_narrative_engine
from ui.charts import build_three_panel
from ui.table import build_opportunity_rows, render_opportunity_table
from utils.timezone import convert_to_HKT

st.set_page_config(
    page_title="CFD Story Dashboard",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=300)
def _cached_fetch_and_run(asset: str, bars_15m: int):
    """Fetch data and run narrative engine once per (asset, bars_15m). Reduces repeated heavy work."""
    data_raw = fetch_all_timeframes(asset, bars_15m=bars_15m)
    if not data_raw or "15M" not in data_raw:
        return None, None, None, None
    df_4h_raw = data_raw["4H"]
    df_1h_raw = data_raw["1H"]
    df_15m_raw = data_raw["15M"]
    result = run_narrative_engine(df_4h_raw, df_1h_raw, df_15m_raw, asset)
    return df_4h_raw, df_1h_raw, df_15m_raw, result


st.title("CFD Story Dashboard")
st.caption("Narrative Coach — where the story currently stands")

# ----- Raw data only for engine -----
asset = st.sidebar.selectbox("Asset", ASSETS, index=0)
bars_15m = st.sidebar.slider("15M bars (fewer = faster load)", 300, 2000, 800, 100)
df_4h_raw, df_1h_raw, df_15m_raw, result = _cached_fetch_and_run(asset, bars_15m)
if df_4h_raw is None or df_15m_raw is None:
    st.warning("No data for selected asset. Add CSV under data/raw/{asset}_15M.csv or use sample.")
    st.stop()

# ----- Data debug info -----
st.write("Data sizes:")
st.write({"4H": len(df_4h_raw), "1H": len(df_1h_raw), "15M": len(df_15m_raw)})

# ----- Engine result (from cache or fresh run) -----
if result is None:
    st.error("Narrative engine returned None.")
    st.stop()
st.write("Engine result keys:", list(result.keys()))

# ----- Visualization: HKT copy only -----
df_4h_viz = convert_to_HKT(df_4h_raw)
df_1h_viz = convert_to_HKT(df_1h_raw)
df_15m_viz = convert_to_HKT(df_15m_raw)

# Align result's 15m outputs to viz index (same length; viz is just tz-converted)
n_15 = len(df_15m_viz)
boundary_price = result.get("boundary_price") or []
if not isinstance(boundary_price, list):
    boundary_price = []
if len(boundary_price) != n_15:
    boundary_price = (boundary_price + [None] * n_15)[:n_15]

# ----- Weekly Opportunity Table (last 4 weeks, HKT display) -----
st.subheader("Weekly Opportunity Log – Last 4 Weeks")
try:
    rows = build_opportunity_rows(result, df_15m_raw, lookback_weeks=4)
    render_opportunity_table(rows)
except Exception as e:
    st.error("Opportunity table failed to render.")
    st.exception(e)
st.markdown("---")

# ----- Three-panel chart (4H stage background, 1H, 15M) -----
st.subheader(f"{asset} – 4H / 1H / 15M")
try:
    fig = build_three_panel(df_4h_viz, df_1h_viz, df_15m_viz, result)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error("Chart rendering failed.")
    st.exception(e)

# ----- Replay Mode (Phase 2 placeholder) -----
st.sidebar.markdown("---")
replay_mode = st.sidebar.checkbox("Replay Mode (Phase 2)", value=False)
if replay_mode:
    st.sidebar.caption("Step candle-by-candle 15M; narrative recalculated each step. Coming in Phase 2.")
