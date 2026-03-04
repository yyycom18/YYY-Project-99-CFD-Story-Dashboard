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

st.title("CFD Story Dashboard")
st.caption("Narrative Coach — where the story currently stands")

# ----- Raw data only for engine -----
asset = st.sidebar.selectbox("Asset", ASSETS, index=0)
data_raw = fetch_all_timeframes(asset, bars_15m=2000)
if not data_raw or "15M" not in data_raw:
    st.warning("No data for selected asset. Add CSV under data/raw/{asset}_15M.csv or use sample.")
    st.stop()

df_4h_raw = data_raw["4H"]
df_1h_raw = data_raw["1H"]
df_15m_raw = data_raw["15M"]

# ----- Engine: raw UTC only -----
result = run_narrative_engine(df_4h_raw, df_1h_raw, df_15m_raw, asset)

# ----- Visualization: HKT copy only -----
df_4h_viz = convert_to_HKT(df_4h_raw)
df_1h_viz = convert_to_HKT(df_1h_raw)
df_15m_viz = convert_to_HKT(df_15m_raw)

# Align result's 15m outputs to viz index (same length; viz is just tz-converted)
# Result was computed on raw; indices match by position
n_15 = len(df_15m_viz)
boundary_price = result.get("boundary_price", [])
if len(boundary_price) != n_15:
    boundary_price = (boundary_price + [None] * n_15)[:n_15]

# ----- Weekly Opportunity Table (last 4 weeks, HKT display) -----
st.subheader("Weekly Opportunity Log – Last 4 Weeks")
rows = build_opportunity_rows(result, df_15m_raw, lookback_weeks=4)
render_opportunity_table(rows)
st.markdown("---")

# ----- Three-panel chart (4H stage background, 1H, 15M) -----
st.subheader(f"{asset} – 4H / 1H / 15M")
fig = build_three_panel(df_4h_viz, df_1h_viz, df_15m_viz, result)
st.plotly_chart(fig, use_container_width=True)

# ----- Replay Mode (Phase 2 placeholder) -----
st.sidebar.markdown("---")
replay_mode = st.sidebar.checkbox("Replay Mode (Phase 2)", value=False)
if replay_mode:
    st.sidebar.caption("Step candle-by-candle 15M; narrative recalculated each step. Coming in Phase 2.")
