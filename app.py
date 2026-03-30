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
import logging
import time
import concurrent.futures

from data.market_data import REQUIRED_OHLC, fetch_all_timeframes, SYMBOL_MAP
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


FULL_BARS_15M = 1500  # reduced default history for engine and full-data operations
DEBUG_MODE = False
if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)


@st.cache_data(show_spinner=False)
def load_data(asset: str, bars_15m: int = FULL_BARS_15M):
    """Cache raw data fetching. Returns dict with '4H','1H','15M' DataFrames."""
    logging.getLogger(__name__).debug("load_data requesting asset=%s lookback_days=%s", asset, bars_15m)
    try:
        data_raw = fetch_all_timeframes(asset, lookback_days=bars_15m)
    except Exception as e:
        raise RuntimeError(f"Data load failed: {e}") from e

    if not data_raw:
        raise RuntimeError(f"Data load failed: fetch returned no data for {asset}")

    for tf in ["15M", "1H", "4H"]:
        df = data_raw.get(tf)
        if df is None:
            logging.getLogger(__name__).debug("load_data: %s missing in data_raw for %s", tf, asset)
            if tf == "15M":
                raise RuntimeError(f"Data load failed: 15M missing for {asset}")
            continue
        try:
            logging.getLogger(__name__).debug("load_data: %s %s shape=%s empty=%s", asset, tf, getattr(df, "shape", None), getattr(df, "empty", None))
        except Exception:
            logging.getLogger(__name__).debug("load_data: %s %s present but could not read shape", asset, tf)

        if df.empty:
            if tf == "15M":
                raise RuntimeError(f"Data load failed: 15M empty for {asset}")
            continue

        missing = [c for c in REQUIRED_OHLC if c not in df.columns]
        if missing:
            raise RuntimeError(
                f"Data load failed: {asset} {tf} missing OHLC {missing}; columns={list(df.columns)}"
            )

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


# ----- Shared label helpers (must be defined before render_* functions) -----
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


def _bias_text(val: int) -> str:
    if val == 1:
        return "Up Bias"
    if val == -1:
        return "Down Bias"
    return "Range"


st.title("CFD Story Dashboard")
st.caption("Narrative Story Monitor — Real market data via yfinance. 4H Season → 1H Wind → 15M Deployment")


def render_story_guide():
    st.title("Story Guide — How to read the CFD Narrative Dashboard")
    st.info("This dashboard provides context, not signals.")
    with st.expander("SECTION 1 — Core Framework", expanded=True):
        st.subheader("Core Framework")
        st.markdown("- **4H Season** → higher timeframe direction (context).")
        st.markdown("- **1H Wind** → short-term structure / momentum.")
        st.markdown("- **Narrative Stage** → market phase (Environment / Trend / Deployment).")
        st.markdown("")
        st.markdown("These descriptors are descriptive (what IS happening), not predictive.")
    with st.expander("SECTION 2 — Bias", expanded=False):
        st.subheader("Bias")
        st.markdown("- **Bias** = directional expectation (NOT current state).")
        st.markdown("- **Up Bias** → bullish expectation.")
        st.markdown("- **Down Bias** → bearish expectation.")
        st.markdown("- **Range** → no confirmed directional edge.")
        st.markdown("")
        st.markdown("**Note:** Bias != Season/Wind. Bias is a decision layer, not a structure layer.")
    with st.expander("SECTION 3 — Zone & Deployment Logic", expanded=False):
        st.subheader("Zone & Deployment Logic")
        st.markdown("- **Zone Level:**")
        st.markdown("  - 0–1 → weak / no institutional presence")
        st.markdown("  - 2 → meaningful reaction zone")
        st.markdown("  - 3+ → strong institutional zone")
        st.markdown("")
        st.markdown("- **Boundary Type:** 0.5 / 0.618 / 0.764 / 0.88 OR 'Zone-Dominant'")
        st.markdown("  - Boundary represents a reaction area, not an entry trigger.")
        st.markdown("")
        st.markdown("- **R:R:** Appears only when a valid deployment setup exists. Must meet minimum 1:1.3.")
        st.markdown("- **Deployment Trigger:** YES → conditions aligned for potential execution. NO → context only.")
    with st.expander("SECTION 4 — Decision Logic", expanded=False):
        st.subheader("Decision Logic")
        st.markdown("- If Stage = Trend AND Bias aligns → watch for opportunity.")
        st.markdown("- If Stage = Deployment → potential execution phase.")
        st.markdown("- If Bias = Range → avoid directional conviction.")
        st.markdown("- Zone Level ≥ 2 → reaction / deployment interest.")
    with st.expander("SECTION 5 — System Philosophy", expanded=False):
        st.subheader("System Philosophy")
        st.markdown("- This dashboard provides CONTEXT, not signals.")
        st.markdown("- It filters opportunities; it does NOT execute trades.")
        st.markdown("- Final decision must be confirmed on TradingView.")


def render_scanner():
    # Scanner limits slider in scanner page (default small for performance)
    assets = list(SYMBOL_MAP.keys())
    total_assets = len(assets)
    scan_limit_local = st.sidebar.slider(
        "Max assets to scan",
        min_value=1,
        max_value=max(1, total_assets),
        value=2,
    )
    st.subheader("Market Scanner")
    # signal quality function (module-local copy)
    def signal_quality_from_result(res: dict) -> (str, bool):
        """
        Return ('green'|'orange'|'red'|'invalid', valid_bool).
        INVALID if zone_level==0 or rr missing or structure missing.
        GREEN if 4H+1H+bias aligned; ORANGE if 2/3 aligned; RED otherwise.
        """
        if not isinstance(res, dict):
            return "invalid", False
        zl = _last_scalar(res.get("zone_level"))
        rr = _last_scalar(res.get("rr"))
        # structure: require narrative_stage present
        ns = _last_scalar(res.get("narrative_stage"))

        # invalid conditions
        try:
            if zl is not None and zl != "-" and int(zl) == 0:
                return "invalid", False
        except Exception:
            pass
        if rr is None or rr == "-" or rr == 0:
            return "invalid", False
        if ns is None or ns == "-":
            return "invalid", False

        # alignment check
        s4 = _last_scalar(res.get("stage_4h"))
        s1 = _last_scalar(res.get("stage_1h"))
        vb4 = _last_scalar(res.get("bias_4h"))
        # normalize to -1/0/1 where possible
        aligns = 0
        try:
            if int(s4) == 1:
                aligns += 1
            if int(s1) == 1:
                aligns += 1
        except Exception:
            pass
        try:
            if int(vb4) == 1:
                aligns += 1
        except Exception:
            pass
        if aligns >= 3:
            return "green", True
        if aligns == 2:
            return "orange", True
        return "red", True

    # reuse existing signal_quality_from_result defined earlier in module
    scanner_rows_local = []
    placeholder = st.empty()
    progress = st.empty()
    partial_table = st.empty()

    # iterate and show partial results immediately; use timed execution per asset
    assets_iter = list(SYMBOL_MAP.keys())
    scan_start_time = time.time()
    with st.spinner("Scanning story state across selected assets…"):
        for i, sym in enumerate(assets_iter):
            if i >= scan_limit_local:
                break
            # progress text
            progress.text(f"Scanning asset {i+1}/{scan_limit_local}: {sym}")

            # Run engine (cached) with per-asset timeout to fail-fast
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_engine_cached, sym, FULL_BARS_15M)
                    try:
                        df4, df1, df15, res = future.result(timeout=12)
                    except concurrent.futures.TimeoutError:
                        placeholder.error(f"{sym} load timeout (>12s); skipping")
                        continue
            except Exception as e:
                placeholder.error(f"Engine error for {sym}: {e}")
                continue

            # Quick validation on returned results
            if df4 is None or df15 is None or res is None or (hasattr(df15, "empty") and df15.empty):
                placeholder.warning(f"No data for {sym}; skipping.")
                scanner_rows_local.append({
                    "Asset": sym,
                    "Market Regime": "N/A",
                    "Season (4H)": "N/A",
                    "Bias (4H)": "N/A",
                    "Wind (1H)": "N/A",
                    "Bias (1H)": "N/A",
                    "Stage (Narrative)": "N/A",
                    "Signal": "⚪ INVALID",
                    "ValidSignal": False,
                })
                partial_table.dataframe(pd.DataFrame(scanner_rows_local), use_container_width=True)
                continue

            s4 = _last_scalar(res.get("stage_4h"))
            s1 = _last_scalar(res.get("stage_1h"))
            ns = _last_scalar(res.get("narrative_stage"))
            season_text = _season_text(s4) if s4 != "-" else "N/A"
            wind_text = _season_text(s1) if s1 != "-" else "N/A"
            stage_text = _narrative_text(ns) if ns != "-" else "N/A"
            regime = _compute_market_regime(df4)
            # Extract bias values (display-friendly)
            vb4 = _last_scalar(res.get("bias_4h"))
            vb1 = _last_scalar(res.get("bias_1h"))
            def _bias_display(val):
                try:
                    if int(val) == 1:
                        return "↑ Up"
                    if int(val) == -1:
                        return "↓ Down"
                except Exception:
                    pass
                return "→ Range"

            quality, valid_signal = signal_quality_from_result(res)
            signal_emoji = {"green":"🟢","orange":"🟠","red":"🔴","invalid":"⚪"}.get(quality, "⚪")
            # Basic signal text (minimal)
            quality_text = {
                "green": "ALIGNED",
                "orange": "PARTIAL",
                "red": "UNALIGNED",
                "invalid": "INVALID"
            }.get(quality, "?")
            signal_display = f"{signal_emoji} {quality_text}"

            scanner_rows_local.append({
                "Asset": sym,
                "Market Regime": regime,
                "Season (4H)": season_text,
                "Bias (4H)": _bias_display(vb4),
                "Wind (1H)": wind_text,
                "Bias (1H)": _bias_display(vb1),
                "Stage (Narrative)": stage_text,
                "Signal": signal_display,
                "ValidSignal": bool(valid_signal),
            })

            # show per-asset success
            if valid_signal:
                placeholder.success(f"{sym} scanned — signal status: {quality.upper()}")
            else:
                placeholder.info(f"{sym} scanned — invalid signal ({quality})")

            # update partial table live
            df_partial = pd.DataFrame(scanner_rows_local)
            partial_table.dataframe(df_partial, use_container_width=True)

            # global safety cap: stop scanning if total elapsed exceeds threshold
            if time.time() - scan_start_time > 25:
                placeholder.warning("Total scanner time exceeded 25 seconds — aborting remaining assets")
                break

    # final rendering (apply styles)
    if scanner_rows_local:
        scanner_df_local = pd.DataFrame(scanner_rows_local)
        # Clear partial table before showing final table (Fix 1)
        try:
            partial_table.empty()
        except Exception:
            pass
        styled_local = (
            scanner_df_local.style.applymap(_regime_color, subset=["Market Regime"])
            .applymap(_season_color, subset=["Season (4H)", "Wind (1H)"])
            .applymap(_stage_color, subset=["Stage (Narrative)"])
        )
        st.dataframe(styled_local, use_container_width=True)
    else:
        st.caption("No assets available for Story Scanner (data fetch may have failed).")


def render_asset_dashboard():
    asset = st.sidebar.selectbox("Asset", list(SYMBOL_MAP.keys()), index=0)
    lookback_days = st.sidebar.slider(
        "Lookback Days",
        5,
        30,
        15,
        1,
        help="Display last N days on charts and tables. Engine uses full cached history; changing this will not re-run the engine.",
    )
    show_swing_markers = st.sidebar.checkbox(
        "Show swing markers",
        value=False,
        help="Toggle plotting of swing high/low markers on charts (visual only).",
    )

    # Fail fast on bad/missing OHLC before long-running spinner + engine
    try:
        data_raw_main = load_data(asset)
    except Exception as e:
        st.error(f"{asset} load failed: {e}")
        st.stop()

    if DEBUG_MODE:
        st.write("DEBUG: data_raw keys:", list(data_raw_main.keys()) if data_raw_main else "missing")
        for tf in ["15M", "1H", "4H"]:
            df_dbg = data_raw_main.get(tf)
            if isinstance(df_dbg, pd.DataFrame):
                st.write(f"DEBUG {tf} shape:", df_dbg.shape, "empty?", df_dbg.empty)
            else:
                st.write(f"DEBUG {tf} missing or invalid")

    with st.spinner("Running narrative engine… (data cached; first run may take a few seconds)"):
        try:
            df_4h_raw, df_1h_raw, df_15m_raw, result = run_engine_cached(asset)
        except Exception as e:
            st.error(f"{e}")
            st.stop()

        if DEBUG_MODE:
            st.write("DEBUG result keys:", list(result.keys()) if isinstance(result, dict) else "result missing")
        for key in ["stage_4h", "stage_1h", "bias_4h", "bias_1h"]:
            val = result.get(key) if isinstance(result, dict) else None
            if val is None:
                if DEBUG_MODE:
                    st.write(f"DEBUG {key} = None")
            else:
                try:
                    if DEBUG_MODE:
                        st.write(f"DEBUG {key} length:", len(val))
                except Exception:
                    if DEBUG_MODE:
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

        if DEBUG_MODE:
            st.write("DEBUG Latest values:")
            st.write("stage_4h:", last_val(result.get("stage_4h") if isinstance(result, dict) else None))
            st.write("bias_4h:", last_val(result.get("bias_4h") if isinstance(result, dict) else None))

    if df_4h_raw is None or df_15m_raw is None:
        st.warning(f"No data available for {asset}. Try a different asset or reduce lookback days.")
        st.stop()

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

    vb4_series = result.get("bias_4h")
    vb1_series = result.get("bias_1h")
    vb4 = _last_scalar(vb4_series)
    vb1 = _last_scalar(vb1_series)

    bias_cols = st.columns(2)
    with bias_cols[0]:
        st.metric("🔺 4H Bias", _bias_text(vb4), help="Market lean on 4H (Up/Down/Range)")
    with bias_cols[1]:
        st.metric("🔺 1H Bias", _bias_text(vb1), help="Market lean on 1H (Up/Down/Range)")

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

    st.subheader("Weekly Opportunity Log – Last 4 Weeks")
    try:
        df_15m_raw_slice = slice_df_by_days(df_15m_raw, lookback_days, "15M")
        rows = build_opportunity_rows(result, df_15m_raw_slice, lookback_weeks=4)
        render_opportunity_table(rows)
    except Exception as e:
        st.error("Opportunity table failed to render.")
        st.exception(e)
    st.markdown("---")

    with st.expander("📘 Market Story Guide", expanded=False):
        st.markdown("**⚠️ This dashboard provides context, not signals.**")
        st.markdown("")
        st.markdown("### 🔍 How to Read This Dashboard")
        st.markdown("")
        st.markdown("**1. Market State**")
        st.markdown("- **4H Season** — higher timeframe direction")
        st.markdown("- **1H Wind** — short-term momentum / structure")
        st.markdown("- **Narrative Stage** — current market phase (Environment → Deployment)")
        st.markdown("")
        st.markdown("**2. Market Bias**")
        st.markdown("- **Up Bias** — bullish expectation")
        st.markdown("- **Down Bias** — bearish expectation")
        st.markdown("- **Range** — no clear directional bias")
        st.markdown("")
        st.markdown("**3. Decision Logic**")
        st.markdown("- If Stage = Trend AND Bias aligns → watch for opportunities")
        st.markdown("- If Stage = Environment → avoid trading (context only)")
        st.markdown("- If Zone Level ≥ 2 → potential reaction / deployment zone")
        st.markdown("")
        st.markdown("**4. Purpose of Dashboard**")
        st.markdown("- This tool is for opportunity filtering and narrative context")
        st.markdown("- NOT for direct entry execution; confirm on TradingView before trading")
        st.markdown("")

    st.subheader(f"{asset} – 4H Season / 1H Wind / 15M Deployment")

    df_15m_raw_slice = slice_df_by_days(df_15m_raw, lookback_days, "15M")
    df_1h_raw_slice = slice_df_by_days(df_1h_raw, lookback_days, "1H")
    df_4h_raw_slice = slice_df_by_days(df_4h_raw, lookback_days, "4H")

    df_4h_viz = convert_to_HKT(df_4h_raw_slice)
    df_1h_viz = convert_to_HKT(df_1h_raw_slice)
    df_15m_viz = convert_to_HKT(df_15m_raw_slice)

    try:
        fig = build_three_panel_figure(df_15m_viz, df_1h_viz, df_4h_viz, result, show_trend=show_swing_markers)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Chart rendering failed.")
        st.exception(e)

    st.sidebar.markdown("---")
    st.sidebar.info("📊 Real market data via yfinance (15M → 1H/4H auto-resample). Cached for fast subsequent loads.")


# Page routing
page = st.sidebar.radio(
    "Navigation",
    ["🧭 Story Guide", "📊 Market Scanner", "🎯 Asset Story", "📚 Docs"],
    index=0,
)

def render_docs():
    """Render documentation pages from /docs with sidebar navigation and next/prev controls."""
    docs_dir = ROOT / "docs"
    if not docs_dir.exists():
        st.error("Documentation directory not found.")
        return

    # Collect markdown files in defined order if present
    docs_files = [
        "00_DASHBOARD_GUIDE.md",
        "01_MARKET_SCANNER.md",
        "02_DATA_LOADING_LOGIC.md",
        "03_SIGNAL_BIAS_EXPLAINED.md",
        "DADA_HANDOFF_UI_INTEGRATION.md",
        "DOCUMENTATION_SUMMARY.md",
    ]
    available = [f for f in docs_files if (docs_dir / f).exists()]
    if not available:
        st.error("No documentation files found in docs/.")
        return

    titles = [p.replace(".md", "").replace("_", " ") for p in available]

    # session state for selected doc index
    if "doc_index" not in st.session_state:
        st.session_state.doc_index = 0

    # Sidebar selector
    sel = st.sidebar.selectbox("Documentation", titles, index=st.session_state.doc_index)
    st.session_state.doc_index = titles.index(sel)

    # Prev / Next buttons
    cols = st.columns([1, 1, 6])
    if cols[0].button("Prev"):
        st.session_state.doc_index = max(0, st.session_state.doc_index - 1)
        sel = titles[st.session_state.doc_index]
    if cols[1].button("Next"):
        st.session_state.doc_index = min(len(titles) - 1, st.session_state.doc_index + 1)
        sel = titles[st.session_state.doc_index]

    # Read and render markdown
    filename = available[st.session_state.doc_index]
    md_path = docs_dir / filename
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception as e:
        st.error(f"Failed to read {filename}: {e}")
        return

    st.markdown(f"### {sel}", unsafe_allow_html=True)
    st.markdown(content)


if page == "🧭 Story Guide":
    render_story_guide()
elif page == "📊 Market Scanner":
    render_scanner()
elif page == "🎯 Asset Story":
    render_asset_dashboard()
elif page == "📚 Docs":
    render_docs()
