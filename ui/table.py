"""
Weekly Opportunity Table. Display in Asia/Hong_Kong only.
Columns: Date (DDMMYYYY), Time (24h HKT), Asset, TF (15M), Narrative Stage, 4H Stage, 1H Stage,
Zone Level, Boundary Type, R:R, Deployment Trigger, Expired Time, Expired Reason.
"""
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from utils.timezone import convert_to_HKT, timestamp_to_HKT_display

STAGE_LABELS = {-1: "Downside", 0: "Neutral", 1: "Upside"}
NARRATIVE_LABELS = {0: "Env", 1: "Trend/Shift", 2: "Retracement", 3: "Deployment", 4: "Liquidity", 5: "Resolution"}


def _format_rr(rr: Any) -> str:
    if rr is None:
        return ""
    try:
        return f"{float(rr):.2f}"
    except (TypeError, ValueError):
        return str(rr)


def build_opportunity_rows(
    result: Dict[str, Any],
    df_15m_raw: pd.DataFrame,
    lookback_weeks: int = 4,
) -> List[Dict[str, Any]]:
    """
    Build opportunity table rows from engine result (raw UTC).
    Only includes bars in last lookback_weeks (calendar weeks) when converted to HKT for display.
    Log first time R:R valid per opportunity; expiry can be added in Phase 2.
    """
    asset = result.get("asset", "")
    deployment_trigger = result.get("deployment_trigger", [])
    rr_list = result.get("rr", [])
    boundary_type = result.get("boundary_type", [])
    narrative_stage = result.get("narrative_stage", [])
    stage_4h_aligned = result.get("stage_4h_aligned", [])
    stage_1h_aligned = result.get("stage_1h_aligned", [])
    zone_level = result.get("zone_level")
    idx = df_15m_raw.index

    rows = []
    n = len(df_15m_raw)
    if n == 0:
        return rows

    # Cut to last 4 weeks in UTC for simplicity (approx)
    from datetime import timedelta
    cutoff = idx[-1] - timedelta(weeks=lookback_weeks)
    if hasattr(cutoff, "tz"):
        pass
    else:
        cutoff = pd.Timestamp(cutoff)

    for i in range(n):
        ts = idx[i]
        if ts < cutoff:
            continue
        trigger = deployment_trigger[i] if i < len(deployment_trigger) else False
        rr = rr_list[i] if i < len(rr_list) else None
        if not trigger and (rr is None or rr < 1.3):
            continue
        bt = boundary_type[i] if i < len(boundary_type) else ""
        ns = narrative_stage[i] if i < len(narrative_stage) else 0
        s4 = int(stage_4h_aligned[i]) if i < len(stage_4h_aligned) else 0
        s1 = int(stage_1h_aligned[i]) if i < len(stage_1h_aligned) else 0
        zl = int(zone_level.iloc[i]) if zone_level is not None and i < len(zone_level) else 0
        try:
            date_str, time_str = timestamp_to_HKT_display(ts)
        except Exception:
            date_str = str(ts)[:10].replace("-", "") if hasattr(ts, "__str__") else ""
            time_str = ""
        rows.append({
            "Date": date_str,
            "Time": time_str,
            "Asset": asset,
            "TF": "15M",
            "Narrative Stage": NARRATIVE_LABELS.get(ns, str(ns)),
            "4H Stage": STAGE_LABELS.get(s4, str(s4)),
            "1H Stage": STAGE_LABELS.get(s1, str(s1)),
            "Zone Level": zl,
            "Boundary Type": bt,
            "R:R": _format_rr(rr),
            "Deployment Trigger": "Yes" if trigger else "No",
            "Expired Time": "",
            "Expired Reason": "",
        })
    return rows


def render_opportunity_table(rows: List[Dict[str, Any]]) -> None:
    """Render weekly opportunity table in Streamlit."""
    if not rows:
        st.caption("No opportunities in the last 4 weeks (15M).")
        return
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
