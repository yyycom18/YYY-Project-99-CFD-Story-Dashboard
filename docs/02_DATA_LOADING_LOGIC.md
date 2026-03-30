# 🔄 Data Loading Logic

**Quick Navigation:** [← Back to Dashboard Guide](00_DASHBOARD_GUIDE.md)

---

## Overview

Understanding how data flows through the dashboard is important for:
- ✅ Knowing why data sometimes fails
- ✅ Understanding why scans take time
- ✅ Recognizing when to skip an asset
- ✅ Trusting the system design

---

## 5-Stage Data Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  STAGE 1: FETCH      → Get price data from yfinance         │
│  ↓                                                            │
│  STAGE 2: VALIDATE   → Check OHLC columns exist & complete  │
│  ↓                                                            │
│  STAGE 3: ENGINE     → Process through narrative logic       │
│  ↓                                                            │
│  STAGE 4: SIGNAL     → Calculate alignment & signal light    │
│  ↓                                                            │
│  STAGE 5: RENDER     → Display in table with colors          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Data Fetch

### What Happens

Dashboard requests historical OHLC data (Open, High, Low, Close) from yfinance for the asset.

**Timeframes fetched:**
- 15-minute (base)
- 1-hour (auto-resampled from 15M)
- 4-hour (auto-resampled from 15M)

### Time Expected

**Per asset:** ~5–10 seconds

**Includes:**
- Network latency
- yfinance server response time
- 10-second timeout (automatic fail-safe)

### Success Criteria

✅ DataFrame returned with data  
✅ Contains Open, High, Low, Close columns  
✅ Has multiple rows (history available)

### Fail Scenarios

#### Scenario A: Network Error
**Reason:** Internet connection lost  
**User sees:** `"XAUUSD load failed: [network error]"`  
**Action:** Dashboard skips asset, continues scanning  

#### Scenario B: Symbol Not Found / Delisted
**Reason:** Symbol doesn't exist or no longer trades  
**User sees:** `"XAUUSD=X: possibly delisted; no price data found"`  
**Action:** Dashboard skips asset, continues  

#### Scenario C: Rate Limited
**Reason:** Too many requests to yfinance in short time  
**User sees:** `"XAUUSD load failed: rate limit exceeded"`  
**Action:** Dashboard skips, tries next asset. (Try again in 1 minute)  

#### Scenario D: Timeout
**Reason:** yfinance taking >10 seconds to respond  
**User sees:** `"XAUUSD load failed: timeout"`  
**Action:** Dashboard skips asset automatically (no infinite wait)

### Fail-Fast Design

⚠️ **Key principle:** If fetch fails, SKIP asset immediately (don't retry)

**Why?**
- No multi-minute delays
- Keep UI responsive
- User can close/refresh if needed
- Prevents cascade failures

---

## Stage 2: Data Validation

### What Happens

Dashboard checks that fetched data is complete and valid.

### Validation Checks

| Check | What It Does | Pass | Fail |
|-------|--------------|------|------|
| **15M exists** | Is 15-minute data present? | ✅ Continue | ❌ Skip |
| **Not empty** | Does DataFrame have rows? | ✅ Continue | ❌ Skip |
| **Has OHLC** | Are Open, High, Low, Close present? | ✅ Continue | ❌ Skip |
| **No NaNs** | Are critical columns filled (not empty)? | ✅ Continue | ⚠️ Warning |

### Time Expected

<1 second (instant check)

### Success Criteria

✅ All checks pass  
✅ Data ready for engine processing

### Fail Scenarios

**"Data invalid: missing 15M"**
- Reason: yfinance didn't include 15M timeframe
- Action: Skip asset (data source issue)

**"Data invalid: 15M empty"**
- Reason: DataFrame has no rows (no history)
- Action: Skip asset (insufficient history)

**"Data invalid: missing cols: [Open, High]"**
- Reason: OHLC columns missing or renamed
- Action: Skip asset (data structure unexpected)

---

## Stage 3: Engine Execution

### What Happens

Narrative engine processes clean OHLC data to compute:

**Outputs:**
- 4H Season (market_stage_at_4h)
- 1H Wind (market_stage_at_1h)
- Narrative Stage (0–5)
- Zone Level (0, 1, or 2)
- Bias 4H & 1H (-1, 0, +1)
- R:R (risk:reward)
- Deployment Trigger (bool)

### Time Expected

**Per asset:** 2–5 seconds

**Breakdown:**
- Swing detection: ~1s
- Structure break: ~0.5s
- Zone calculation: ~1s
- Narrative logic: ~0.5–1s
- R:R calculation: <0.5s

### Caching

⚡ **Important:** Engine runs ONCE per asset per session

**Why caching?**
- User might click same asset multiple times
- Avoid redundant computation
- Keep UI responsive

**How it works:**
```python
@st.cache_data
def run_engine_cached(asset):
    # First call: compute everything
    # Second call: return cached result instantly
```

### Success Criteria

✅ Engine completes without error  
✅ Returns all required fields  
✅ No inf/NaN in final outputs

### Fail Scenarios

**"Engine error for EURUSD: [error]"**
- Reason: Logic error in engine (edge case)
- Action: Skip asset, continue scanning
- Note: Rare; usually edge case in swing detection

**"No data for GBPUSD; skipping"**
- Reason: Engine ran but returned None/incomplete result
- Action: Skip asset silently
- Note: Rare; usually means data quality issue

---

## Stage 4: Signal Calculation

### What Happens

System compares engine outputs to determine market alignment.

**Logic:**
```
Count how many of these are TRUE:
  ✅ 4H Season = +1 (Upside)?
  ✅ 1H Wind = +1 (Upside)?
  ✅ 4H Bias = +1 (Up)?

Result:
  3/3 → 🟢 GREEN
  2/3 → 🟠 ORANGE
  0–1 → 🔴 RED
```

**Additional checks (force 🔴 RED if true):**
- Zone Level = 0 (no structural confirmation)
- R:R missing or 0 (no valid opportunity)
- Narrative Stage missing (incomplete analysis)

### Time Expected

<1 second (math only)

### Success Criteria

✅ Signal determined (green/orange/red/invalid)  
✅ Valid = clear decision

### Examples

**GREEN Signal (3/3)**
```
Input:  4H Season = +1 ✅
        1H Wind = +1 ✅
        4H Bias = +1 ✅
Output: 🟢 GREEN (aligned)
```

**ORANGE Signal (2/3)**
```
Input:  4H Season = +1 ✅
        1H Wind = +1 ✅
        4H Bias = 0 ❌
Output: 🟠 ORANGE (partial)
```

**RED Signal (0–1 aligned)**
```
Input:  4H Season = +1 ✅
        1H Wind = -1 ❌
        4H Bias = -1 ❌
Output: 🔴 RED (conflicted)
```

**INVALID Signal (missing data)**
```
Input:  Zone Level = 0 ❌
        or R:R = None ❌
        or Stage missing ❌
Output: ⚪ INVALID (can't assess)
```

---

## Stage 5: UI Render

### What Happens

Final row added to scanner table with:
- Asset name
- Market regime
- Season + Bias
- Wind + Bias
- Stage
- Signal light
- Colors applied

### Time Expected

~100ms (instant to user)

### Live Updates

📌 **Key feature:** Partial table updates AS each asset completes

**User experience:**
1. Asset 1 finishes → Row 1 appears
2. Asset 2 finishes → Row 2 appears
3. Asset 3 finishes → Row 3 appears
4. After all done → Final styled table replaces partial

**Why this matters:**
- ✅ User sees progress (feels responsive)
- ✅ Partial results available immediately
- ✅ Can act on first 1–2 assets while 3rd loads

### Display Logic

**Colors:**
- Green backgrounds for Upside/aligned
- Red backgrounds for Downside/conflicted
- Gray for neutral/range

**Font:**
- Bold signal lights (stands out)
- Regular text for details

---

## Performance Timeline

### Real Example: Scan 3 Assets

```
START: 00:00
├─ Asset 1 (XAUUSD)
│  ├─ Fetch: 00:00–00:08 ................ (8s)
│  ├─ Validate: 00:08–00:09 ............ (1s)
│  ├─ Engine: 00:09–00:12 ............. (3s)
│  ├─ Signal: 00:12–00:13 ............. (1s)
│  ├─ Render: 00:13–00:14 ............. (1s)
│  └─ Subtotal: 13 seconds ✅
│
├─ Asset 2 (EURUSD)
│  └─ Same process: 13 seconds ✅
│
├─ Asset 3 (GBPUSD)
│  └─ Same process: 13 seconds ✅
│
└─ TOTAL: ~39 seconds (parallel would be ~13s, but sequential for clarity)
```

**Expected total:** 15–40 seconds (depending on network)

---

## Error Handling Flow

```
┌─────────────────────────────────────────┐
│ START SCAN                               │
└────────────┬────────────────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ Fetch Data       │
    └────┬─────────┬──┘
         │         │
    ERROR│         │ OK
         ▼         ▼
    Show    │   Validate
    Error   │   Data
         │   ▼
         │   ┌──────────────┐
         │   │Invalid?      │
         │   └┬────────┬───┘
         │   │         │
         │ERROR│       │ OK
         │   ▼         ▼
         │ Show    Run
         │Warning   Engine
         │   │   ▼
         │   │   ┌──────────────┐
         │   │   │Engine Error? │
         │   │   └┬──────┬─────┘
         │   │   │      │
         │ ERROR  │      │ OK
         │   ▼    ▼      ▼
         │ Show  SKIP   Calc
         │Error        Signal
         │   │         │
         └───┼─────────┼────────┐
             │         │        │
             └────┬────┴────┬───┘
                  │         │
              Add to   Display
              Table    in UI
              │         │
              └────┬────┘
                   ▼
            SCAN COMPLETE
```

---

## Fail-Fast Design (Core Principle)

### Why Fail-Fast?

**Problem without it:**
- Fetch fails → retry → wait 10s
- Retry fails → retry again → wait 10s
- Total: 30+ seconds per asset
- User gives up, closes dashboard

**Solution with it:**
- Fetch fails → skip immediately
- Continue to next asset
- User sees partial results
- Non-blocking experience

### Where Fail-Fast Applied

| Stage | Behavior |
|-------|----------|
| **Fetch** | Timeout 10s, then skip (no retry) |
| **Validate** | Check once, skip if invalid |
| **Engine** | Run once, skip if error |
| **Signal** | Calculate immediately |
| **Render** | Display instantly |

---

## Data Quality Checks

### What Ensures Data Quality?

1. **yfinance reliability**
   - Major symbols: Very reliable
   - Minor symbols: Less reliable
   - Delisted: No data

2. **OHLC validation**
   - Must have Open, High, Low, Close
   - Must be numeric
   - Must have history (>50 bars)

3. **Engine robustness**
   - Handles missing swings
   - Handles partial data
   - Returns safe defaults (not crashes)

### What Dashboard Doesn't Validate

❌ Price accuracy (trusts yfinance)  
❌ Bid/ask spreads (outside scope)  
❌ Trading hours (UTC assumed)  
❌ Corporate actions (stock splits, etc)

---

## Advanced: How Resampling Works

### Why Resampling?

Engine needs:
- 4H data (for Season)
- 1H data (for Wind)
- 15M data (for Deployment)

yfinance only has:
- 15M base data

### Solution: Auto-Resampling

```python
df_15m = fetch_data(asset, "15M")  # Base data
df_1h = resample_15m_to_1h(df_15m)  # Auto-create
df_4h = resample_15m_to_4h(df_15m)  # Auto-create
```

**How resampling works:**
```
Candle combining:
- Open: First 15M candle open
- High: Max high of all 15M candles
- Low: Min low of all 15M candles
- Close: Last 15M candle close
```

**Example:**
```
15M candles 00:00–00:15 + 00:15–00:30 + ... + 00:45–01:00
→ Combined into 1H candle 00:00–01:00
```

---

## Troubleshooting Data Issues

### "Always shows INVALID for XAUUSD"

**Possible causes:**
1. Zone Level consistently 0 (no structure)
2. R:R always missing (no target swing)
3. Data quality issue (gaps in history)

**Solutions:**
- Try different asset
- Increase lookback days
- Check yfinance data availability

### "Signal keeps changing"

**Normal behavior:**
- Market evolves
- Stage, zone, or bias changes
- Signal updates accordingly

**Not a bug—it's working correctly**

### "Engine error: 'NaN' in data"

**Likely cause:** Missing or invalid prices  
**Solution:** Refresh and retry  
**If persistent:** Asset may be delisted

---

## Summary: Data Pipeline

| Stage | Time | Failure | Next |
|-------|------|---------|------|
| **Fetch** | 5–10s | Skip | Validate |
| **Validate** | <1s | Skip | Engine |
| **Engine** | 2–5s | Skip | Signal |
| **Signal** | <1s | Reclassify | Render |
| **Render** | ~100ms | Try again | Display |

**Total per asset:** ~10–15 seconds ✓

**Total for 3 assets:** ~15–40 seconds ✓

---

**Next:** [← Back to Dashboard Guide](00_DASHBOARD_GUIDE.md)

