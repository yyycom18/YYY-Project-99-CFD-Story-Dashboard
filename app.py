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

# ----- Narrative Summary Panel (current state = last bar) -----
st.subheader("Current Narrative State")
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
s15 = result.get("stage_15m")
ns = result.get("narrative_stage")
zl = result.get("zone_level")
bt = result.get("boundary_type")
rr_list = result.get("rr")
dt_list = result.get("deployment_trigger")

col1, col2, col3 = st.columns(3)
with col1:
    v4 = _last_scalar(s4h)
    st.metric("4H Season", _STAGE_LABELS.get(int(v4), str(v4)) if v4 != "-" else v4)
    v1 = _last_scalar(s1h)
    st.metric("1H Wind", _STAGE_LABELS.get(int(v1), str(v1)) if v1 != "-" else v1)
    v15 = _last_scalar(s15)
    st.metric("15M Structure", _STAGE_LABELS.get(int(v15), str(v15)) if v15 != "-" else v15)
with col2:
    vn = _last_scalar(ns)
    st.metric("Narrative Stage", _NARRATIVE_LABELS.get(int(vn), str(vn)) if vn != "-" else vn)
    vzl = _last_scalar(zl)
    st.metric("Zone Level", str(int(vzl)) if isinstance(vzl, (int, float)) else vzl)
    vbt = _last_scalar(bt)
    st.metric("Boundary Type", str(vbt) if vbt != "-" else vbt)
with col3:
    vrr = _last_scalar(rr_list)
    rr_display = f"{float(vrr):.2f}" if isinstance(vrr, (int, float)) else (vrr if vrr != "-" else "-")
    st.metric("R:R", rr_display)
    vdt = _last_scalar(dt_list)
    st.metric("Deployment Trigger", "Yes" if vdt is True else ("No" if vdt is False else str(vdt)))

st.markdown("---")

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
