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


FULL_BARS_15M = 4000  # default history for engine and full-data operations


@st.cache_data(show_spinner=False)
def load_data(asset: str, bars_15m: int = FULL_BARS_15M):
    """Cache raw data fetching. Returns dict with '4H','1H','15M' DataFrames."""
    # fetch_all_timeframes expects parameter name `lookback_days`
    print(f"DEBUG load_data: requesting asset={asset}, lookback_days={bars_15m}")
    data_raw = fetch_all_timeframes(asset, lookback_days=bars_15m)
    # Debug prints
    if not data_raw:
        raise RuntimeError(f"load_data: fetch_all_timeframes returned empty for {asset}")
    for tf in ["15M", "1H", "4H"]:
        df = data_raw.get(tf)
        if df is None:
            print(f"DEBUG load_data: {tf} missing in data_raw for {asset}")
        else:
            try:
                print(f"DEBUG load_data: {asset} {tf} shape={df.shape}, empty={df.empty}")
            except Exception:
                print(f"DEBUG load_data: {asset} {tf} present but could not read shape")
    # If 15M is empty, raise clear error so caller can surface it
    df15 = data_raw.get("15M")
    if df15 is None or df15.empty:
        raise RuntimeError(f"load_data: 15M data empty for {asset} after fetch. See logs for fetch failures.")
    return data_raw


@st.cache_data(show_spinner=False)
def run_engine_cached(asset: str, bars_15m: int = FULL_BARS_15M):
    """
    Run narrative engine on the full cached dataset. Cache keyed by asset+bars_15m.
    Returns: df_4h_raw, df_1h_raw, df_15m_raw, result
    """
    data_raw = load_data(asset, bars_15m=bars_15m)
    if not data_raw or "15M" not in data_raw:
        return None, None, None, None
    df_4h_raw = data_raw["4H"]
    df_1h_raw = data_raw["1H"]
    df_15m_raw = data_raw["15M"]
    result = run_narrative_engine(df_4h_raw, df_1h_raw, df_15m_raw, asset)
    return df_4h_raw, df_1h_raw, df_15m_raw, result


def slice_df_by_days(df: pd.DataFrame, days: int, tf: str) -> pd.DataFrame:
    """Return a tail slice of df corresponding to approx `days` for timeframe tf.
    tf: one of '15M','1H','4H'. Uses simple bars-per-day heuristics (15M=96,1H=24,4H=6).
    """
    if df is None or df.empty:
        return df
    bars_per_day = {"15M": 24 * 4, "1H": 24, "4H": 6}.get(tf, 24)
    n = max(1, int(days * bars_per_day))
    return df.tail(n)


st.title("CFD Story Dashboard")
st.caption("Narrative Story Monitor — Real market data via yfinance. 4H Season → 1H Wind → 15M Deployment")

# Sidebar configuration
asset = st.sidebar.selectbox("Asset", list(SYMBOL_MAP.keys()), index=0)

# Lookback days: chart display and engine history
lookback_days = st.sidebar.slider(
    "Lookback Days",
    5,
    30,
    15,
    1,
    help="Display last N days on charts and tables. Engine uses full cached history; changing this will not re-run the engine.",
)

# Scanner limits: avoid running engine for all assets at once (performance)
# Default max 3 assets; user can adjust up to min(8, total assets)
max_assets_default = 3
max_assets_upper = min(8, max(1, len(SYMBOL_MAP)))
scan_limit = st.sidebar.slider("Max assets to scan", 1, max_assets_upper, max_assets_default)

# ----- Shared label helpers -----
_STAGE_LABELS = {-1: "Downside", 0: "Neutral", 1: "Upside"}
_NARRATIVE_LABELS = {
    0: "Environment",
    1: "Trend",
    2: "Retracement",
    3: "Deployment",
    4: "Liquidity",
    5: "Resolution",
}


def _last_scalar(x, default="-"):
    """Get last value from series or list for display."""
    if x is None:
        return default
    if hasattr(x, "iloc"):
        return x.iloc[-1] if len(x) else default
    if isinstance(x, list):
        return x[-1] if len(x) else default
    return x


def _season_text(stage_val) -> str:
    """Map numeric stage to Season/Wind text."""
    try:
        return _STAGE_LABELS.get(int(stage_val), str(stage_val))
    except Exception:
        return str(stage_val)


def _narrative_text(stage_val) -> str:
    """Map narrative stage 0–5 to descriptive label."""
    try:
        return _NARRATIVE_LABELS.get(int(stage_val), str(stage_val))
    except Exception:
        return str(stage_val)


def _season_color(val: str) -> str:
    """Color rule for Season / Wind columns."""
    if val == "Upside":
        return "background-color: #dcfce7; color: #166534;"  # green
    if val == "Downside":
        return "background-color: #fee2e2; color: #b91c1c;"  # red
    if val == "Neutral":
        return "background-color: #f3f4f6; color: #4b5563;"  # gray
    return ""


def _stage_color(val: str) -> str:
    """Color rule for narrative Stage column."""
    if val == "Environment":
        return "background-color: #f3f4f6; color: #4b5563;"  # gray
    if val == "Trend":
        return "background-color: #dbeafe; color: #1d4ed8;"  # blue
    if val == "Retracement":
        return "background-color: #ffedd5; color: #c2410c;"  # orange
    if val == "Deployment":
        return "background-color: #dcfce7; color: #166534;"  # green
    if val == "Liquidity":
        return "background-color: #f5f3ff; color: #6b21a8;"  # purple
    if val == "Resolution":
        return "background-color: #e5e7eb; color: #374151;"  # neutral
    return ""


def _regime_color(val: str) -> str:
    """Color rule for Market Regime column."""
    if val == "Compression":
        return "background-color: #f3f4f6; color: #4b5563;"  # gray
    if val == "Normal":
        return "background-color: #dbeafe; color: #1d4ed8;"  # blue
    if val == "Wide Range":
        return "background-color: #ffedd5; color: #c2410c;"  # orange
    return ""


def _compute_market_regime(df_4h_raw: pd.DataFrame) -> str:
    """
    Compute Market Regime (market width) from 4H data.

    1) Use last ~20 days ≈ 120 bars.
    2) range = highest_high - lowest_low over last 120 bars.
    3) ATR(14) using standard true range.
    4) width_ratio = range / atr.
    5) Classify into Compression / Normal / Wide Range.
    """
    if df_4h_raw is None or df_4h_raw.empty:
        return "N/A"

    df = df_4h_raw.sort_index()
    if len(df) < 30:
        return "N/A"

    window = 120
    recent = df.tail(window)
    highest_high = recent["High"].max() if "High" in recent.columns else recent["high"].max()
    lowest_low = recent["Low"].min() if "Low" in recent.columns else recent["low"].min()
    mkt_range = float(highest_high - lowest_low)
    if mkt_range <= 0:
        return "Compression"

    # ATR(14) – compute true range then rolling mean.
    hl = (df["High"] - df["Low"]) if "High" in df.columns else (df["high"] - df["low"])
    close_col = "Close" if "Close" in df.columns else "close"
    h_cp = (df["High"] - df[close_col].shift()).abs() if "High" in df.columns else (df["high"] - df[close_col].shift()).abs()
    l_cp = (df["Low"] - df[close_col].shift()).abs() if "Low" in df.columns else (df["low"] - df[close_col].shift()).abs()
    tr = pd.concat([hl, h_cp, l_cp], axis=1).max(axis=1)
    atr_series = tr.rolling(window=14, min_periods=14).mean()
    atr = float(atr_series.tail(window).iloc[-1]) if not atr_series.tail(window).isna().all() else 0.0

    if atr <= 0:
        return "Compression"

    width_ratio = mkt_range / atr

    if width_ratio < 4:
        return "Compression"
    if width_ratio < 8:
        return "Normal"
    return "Wide Range"


# ----- Story Scanner: multi-asset narrative overview -----
st.subheader("Story Scanner")
scanner_rows = []

with st.spinner("Scanning story state across all assets…"):
    for i, sym in enumerate(SYMBOL_MAP.keys()):
        if i >= scan_limit:
            break
        st.write(f"Scanning {sym}...")
        # Each asset fetches its own data (cached) and runs its cached narrative engine
        # Debug: inspect cached raw data before engine
        try:
            data_raw_dbg = load_data(sym)
        except Exception as e:
            st.error(f"Data load error for {sym}: {e}")
            continue
        st.write(f"DEBUG: data_raw keys for {sym}:", list(data_raw_dbg.keys()) if data_raw_dbg else "missing")
        for tf in ["15M", "1H", "4H"]:
            if data_raw_dbg and tf in data_raw_dbg and isinstance(data_raw_dbg[tf], pd.DataFrame):
                st.write(f"DEBUG {sym} {tf} shape:", data_raw_dbg[tf].shape)
            else:
                st.write(f"DEBUG {sym} {tf} missing or not a DataFrame")

        try:
            df4, df1, df15, res = run_engine_cached(sym)
        except Exception as e:
            st.error(f"Engine error for {sym}: {e}")
            continue

        if df4 is None or df15 is None or res is None:
            st.warning(f"No data for {sym}; skipping.")
            continue

        s4 = _last_scalar(res.get("stage_4h"))
        s1 = _last_scalar(res.get("stage_1h"))
        ns = _last_scalar(res.get("narrative_stage"))

        season_text = _season_text(s4) if s4 != "-" else "N/A"
        wind_text = _season_text(s1) if s1 != "-" else "N/A"
        stage_text = _narrative_text(ns) if ns != "-" else "N/A"

        regime = _compute_market_regime(df4)

        scanner_rows.append(
            {
                "Asset": sym,
                "Market Regime": regime,
                "Season (4H)": season_text,
                "Wind (1H)": wind_text,
                "Stage (Narrative)": stage_text,
            }
        )

if scanner_rows:
    scanner_df = pd.DataFrame(scanner_rows)
    styled = (
        scanner_df.style.applymap(_regime_color, subset=["Market Regime"])
        .applymap(_season_color, subset=["Season (4H)", "Wind (1H)"])
        .applymap(_stage_color, subset=["Stage (Narrative)"])
    )
    st.dataframe(styled, use_container_width=True)
else:
    st.caption("No assets available for Story Scanner (data fetch may have failed).")

st.markdown("---")

with st.spinner("Loading real market data and running narrative engine… (~10–20s first time, instant on cache)"):
    # Debug: inspect raw data fetched
    try:
        data_raw_main = load_data(asset)
    except Exception as e:
        st.error(f"Data load error for {asset}: {e}")
        st.stop()
    st.write("DEBUG: data_raw keys:", list(data_raw_main.keys()) if data_raw_main else "missing")
    if data_raw_main:
        for tf in ["15M", "1H", "4H"]:
            df_dbg = data_raw_main.get(tf)
            if isinstance(df_dbg, pd.DataFrame):
                st.write(f"DEBUG {tf} shape:", df_dbg.shape)
                st.write(f"DEBUG {tf} empty?", df_dbg.empty)
            else:
                st.write(f"DEBUG {tf} missing or invalid")

    try:
        df_4h_raw, df_1h_raw, df_15m_raw, result = run_engine_cached(asset)
    except Exception as e:
        st.error(f"Engine error for {asset}: {e}")
        st.stop()

    # Debug engine output
    st.write("DEBUG result keys:", list(result.keys()) if isinstance(result, dict) else "result missing")
    for key in ["stage_4h", "stage_1h", "bias_4h", "bias_1h"]:
        val = result.get(key) if isinstance(result, dict) else None
        if val is None:
            st.write(f"DEBUG {key} = None")
        else:
            try:
                st.write(f"DEBUG {key} length:", len(val))
            except Exception:
                st.write(f"DEBUG {key} present (non-iterable)")

    def last_val(series):
        try:
            if series is None:
                return None
            if hasattr(series, "iloc"):
                return series.iloc[-1]
            if isinstance(series, list):
                return series[-1] if len(series) else None
            return series
        except Exception:
            return None

    st.write("DEBUG Latest values:")
    st.write("stage_4h:", last_val(result.get("stage_4h") if isinstance(result, dict) else None))
    st.write("bias_4h:", last_val(result.get("bias_4h") if isinstance(result, dict) else None))

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

# ----- Market Bias display (new) -----
def _bias_text(val: int) -> str:
    if val == 1:
        return "Up Bias"
    if val == -1:
        return "Down Bias"
    return "Range"

# Last-known bias values from engine result
vb4_series = result.get("bias_4h")
vb1_series = result.get("bias_1h")
vb4 = _last_scalar(vb4_series)
vb1 = _last_scalar(vb1_series)

bias_cols = st.columns(2)
with bias_cols[0]:
    st.metric("🔺 4H Bias", _bias_text(vb4), help="Market lean on 4H (Up/Down/Range)")
with bias_cols[1]:
    st.metric("🔺 1H Bias", _bias_text(vb1), help="Market lean on 1H (Up/Down/Range)")

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
    # Slice 15M raw for table rendering to avoid reprocessing entire history
    df_15m_raw_slice = slice_df_by_days(df_15m_raw, lookback_days, "15M")
    rows = build_opportunity_rows(result, df_15m_raw_slice, lookback_weeks=4)
    render_opportunity_table(rows)
except Exception as e:
    st.error("Opportunity table failed to render.")
    st.exception(e)
st.markdown("---")

# ----- Three-panel chart: Real market data (HKT viz) -----
st.subheader(f"{asset} – 4H Season / 1H Wind / 15M Deployment")

# Slice raw data for visualization only (engine used full-history cached results)
df_15m_raw_slice = slice_df_by_days(df_15m_raw, lookback_days, "15M")
df_1h_raw_slice = slice_df_by_days(df_1h_raw, lookback_days, "1H")
df_4h_raw_slice = slice_df_by_days(df_4h_raw, lookback_days, "4H")

# Convert to HKT for visualization only
df_4h_viz = convert_to_HKT(df_4h_raw_slice)
df_1h_viz = convert_to_HKT(df_1h_raw_slice)
df_15m_viz = convert_to_HKT(df_15m_raw_slice)

try:
    fig = build_three_panel_figure(df_15m_viz, df_1h_viz, df_4h_viz, result)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error("Chart rendering failed.")
    st.exception(e)

st.sidebar.markdown("---")
st.sidebar.info("📊 Real market data via yfinance (15M → 1H/4H auto-resample). Cached for fast subsequent loads.")
