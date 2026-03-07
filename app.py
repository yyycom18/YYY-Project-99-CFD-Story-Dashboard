"""
CFD Story Dashboard — Narrative Story Monitor.
Shows where the market story stands across 4H Season, 1H Wind, 15M Deployment.
Raw data → engine only. All visualization uses HKT (UTC+8) via convert_to_HKT().
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from data.fetch import ASSETS, fetch_all_timeframes
from engine.narrative import run_narrative_engine
from ui.charts import build_three_panel
from ui.table import build_opportunity_rows, render_opportunity_table
from utils.timezone import convert_to_HKT, timestamp_to_HKT_display

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
st.caption("Narrative Story Monitor — where the market story currently stands (4H Season → 1H Wind → 15M Deployment)")

# Time window: bars to show per timeframe (chart display only; engine uses full history)
def window_to_bars(weeks: int):
    """Return (bars_15m, bars_1h, bars_4h) for chart display range. 15M: 672 bars/week."""
    bars_15m = weeks * 7 * 24 * 4   # 672 per week
    bars_1h = weeks * 7 * 24        # 168 per week
    bars_4h = weeks * 7 * 6         # 42 per week
    return bars_15m, bars_1h, bars_4h

# ----- Raw data only for engine -----
asset = st.sidebar.selectbox("Asset", ASSETS, index=0)
# Load enough bars so Time Window (1/2/4 weeks) shows different ranges: 4 weeks = 2688 bars
bars_15m = st.sidebar.slider("15M bars (fewer = faster load)", 700, 3500, 2800, 100)

# Time Window: chart display range only (does not change engine history)
time_window_label = st.sidebar.selectbox(
    "Time Window",
    ["1 week", "2 weeks", "4 weeks"],
    index=2,
    help="Chart display range only. Engine uses full history.",
)
time_window_weeks = {"1 week": 1, "2 weeks": 2, "4 weeks": 4}.get(time_window_label, 4)

# Auto Log: log narrative changes when enabled
auto_log = st.sidebar.checkbox("Auto Log", value=False, help="Log stage and deployment trigger changes above charts.")
if "narrative_log" not in st.session_state:
    st.session_state.narrative_log = []
if "narrative_prev_state" not in st.session_state:
    st.session_state.narrative_prev_state = {}

df_4h_raw, df_1h_raw, df_15m_raw, result = _cached_fetch_and_run(asset, bars_15m)
if df_4h_raw is None or df_15m_raw is None:
    st.warning("No data for selected asset. Add CSV under data/raw/{asset}_15M.csv or use sample.")
    st.stop()

# ----- Engine result (from cache or fresh run) -----
if result is None:
    st.error("Narrative engine returned None.")
    st.stop()
with st.expander("Data & engine info", expanded=False):
    st.write("Data sizes:", {"4H": len(df_4h_raw), "1H": len(df_1h_raw), "15M": len(df_15m_raw)})
    st.write("Engine result keys:", list(result.keys()))

# ----- Narrative Summary Panel: story position (primary + secondary) -----
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

# ----- Auto Log: append on narrative change -----
if auto_log and result:
    prev = st.session_state.narrative_prev_state
    cur_4h = int(v4) if v4 != "-" and isinstance(v4, (int, float)) else None
    cur_1h = int(v1) if v1 != "-" and isinstance(v1, (int, float)) else None
    cur_ns = int(vn) if vn != "-" and isinstance(vn, (int, float)) else None
    cur_dt = bool(vdt) if vdt is True or vdt is False else None
    stage_changes = []
    if prev.get("stage_4h") is not None and cur_4h is not None and prev.get("stage_4h") != cur_4h:
        stage_changes.append(f"4H: {_STAGE_LABELS.get(prev['stage_4h'], '?')}→{_STAGE_LABELS.get(cur_4h, '?')}")
    if prev.get("stage_1h") is not None and cur_1h is not None and prev.get("stage_1h") != cur_1h:
        stage_changes.append(f"1H: {_STAGE_LABELS.get(prev['stage_1h'], '?')}→{_STAGE_LABELS.get(cur_1h, '?')}")
    if prev.get("narrative_stage") is not None and cur_ns is not None and prev.get("narrative_stage") != cur_ns:
        stage_changes.append(f"Narrative: {_NARRATIVE_LABELS.get(prev['narrative_stage'], '?')}→{_NARRATIVE_LABELS.get(cur_ns, '?')}")
    if prev.get("deployment_trigger") is not None and cur_dt is not None and prev.get("deployment_trigger") != cur_dt:
        stage_changes.append("Deployment: " + ("No→Yes" if cur_dt else "Yes→No"))
    if stage_changes:
        try:
            ts = df_15m_raw.index[-1]
            date_str, time_str = timestamp_to_HKT_display(ts)
            st.session_state.narrative_log.append({
                "Time": f"{date_str} {time_str}",
                "Asset": asset,
                "Stage Change": " | ".join(stage_changes),
                "Deployment Trigger": "Yes" if cur_dt else "No",
            })
        except Exception:
            pass
    st.session_state.narrative_prev_state = {
        "stage_4h": cur_4h,
        "stage_1h": cur_1h,
        "narrative_stage": cur_ns,
        "deployment_trigger": cur_dt,
    }

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

# ----- Auto Log table (above charts, when enabled) -----
if auto_log and st.session_state.narrative_log:
    st.subheader("Narrative change log")
    log_df = pd.DataFrame(st.session_state.narrative_log[-50:])  # last 50 entries
    st.dataframe(log_df, use_container_width=True, hide_index=True, height=min(200, 52 + 35 * len(log_df)))
    st.markdown("---")

# ----- Three-panel chart: display range from Time Window (HKT viz only) -----
st.subheader(f"{asset} – 4H Season / 1H Wind / 15M Deployment")
# Apply Time Window via tail(last_n_bars); chart display only, engine unchanged
last_n_15m, last_n_1h, last_n_4h = window_to_bars(time_window_weeks)
# Cap to available data so 1w / 2w / 4w show different ranges when bars_15m >= 2688
n_15 = min(last_n_15m, len(df_15m_viz))
n_1h = min(last_n_1h, len(df_1h_viz))
n_4h = min(last_n_4h, len(df_4h_viz))
df_4h_display = df_4h_viz.tail(n_4h)
df_1h_display = df_1h_viz.tail(n_1h)
df_15m_display = df_15m_viz.tail(n_15)
try:
    fig = build_three_panel(df_4h_display, df_1h_display, df_15m_display, result)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error("Chart rendering failed.")
    st.exception(e)

# ----- Replay Mode (Phase 2 placeholder) -----
st.sidebar.markdown("---")
replay_mode = st.sidebar.checkbox("Replay Mode (Phase 2)", value=False)
if replay_mode:
    st.sidebar.caption("Step candle-by-candle 15M; narrative recalculated each step. Coming in Phase 2.")
