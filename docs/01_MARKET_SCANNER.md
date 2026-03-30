# 📊 Market Scanner Guide

**Quick Navigation:** [← Back to Dashboard Guide](00_DASHBOARD_GUIDE.md)

---

## Overview

The **Market Scanner** is your entry point to the dashboard. It provides a real-time snapshot of market state across multiple assets simultaneously.

**Purpose:** Quickly identify which assets have clear, aligned stories worth exploring deeper.

---

## 📈 Scanner Table Explained

### What Each Column Means

#### **Asset**
Currency pair or index (XAUUSD, EURUSD, GBPUSD, etc.)

---

#### **Market Regime**
Overall composite direction (not tied to specific timeframe)

**Values:**
- 🟢 **Upside** — More higher highs/lows than lower highs/lows
- 🔴 **Downside** — More lower highs/lows than higher highs/lows
- ⚪ **Range** — No clear directional bias

---

#### **Season (4H)**
Higher timeframe market state

**Values:**
- 🟢 **Upside** — 4H is bullish (context)
- 🔴 **Downside** — 4H is bearish
- ⚪ **Neutral** — No 4H structure yet

**What it means:** "Where is the larger market going?"

---

#### **Bias (4H)**
4H directional expectation (separate from structure)

**Values:**
- ↑ **Up** — Expecting higher prices
- ↓ **Down** — Expecting lower prices
- → **Range** — No confirmed edge

---

#### **Wind (1H)**
Short-term momentum direction

**Values:**
- 🟢 **Upside** — 1H momentum bullish
- 🔴 **Downside** — 1H momentum bearish
- ⚪ **Neutral** — 1H unclear

**What it means:** "Is short-term moving with or against 4H?"

---

#### **Bias (1H)**
1H directional expectation

**Values:** ↑ / ↓ / →

---

#### **Stage (Narrative)**
Current story phase

**Values:**
- 0: **Environment** — Forming, no trend
- 1: **Trend** — Direction confirmed
- 2: **Retracement** — Pullback in trend
- 3: **Deployment** — Setup ready, R:R good
- 4: **Liquidity** — Institutional activity
- 5: **Resolution** — Trade completing

---

#### **Signal**
Overall alignment status (your decision indicator)

**Values:**
- 🟢 **GREEN** — 3/3 conditions aligned (best case)
- 🟠 **ORANGE** — 2/3 aligned (partial)
- 🔴 **RED** — 0–1 aligned (conflicted)
- ⚪ **INVALID** — Missing data

---

## 🎯 How to Read the Scanner

### Step 1: Scan & Look

1. Dashboard loads with scanner pre-scan
2. Watch progress bar as assets load
3. Once complete, review signal lights

### Step 2: Identify Candidates

**Look for:**
- 🟢 GREEN signals (aligned stories)
- 🟠 ORANGE signals (watch for alignment)

**Avoid:**
- 🔴 RED signals (conflicted)
- ⚪ INVALID signals (data issues)

### Step 3: Quick Check (2-second rules)

**GREEN signal?**
- ✅ Season matches Wind? → Likely same direction
- ✅ Both Biases up (↑/↑)? → Expectation aligned
- → **VERDICT:** High quality setup, inspect deeper

**ORANGE signal?**
- ✅ Is the 2/3 the important ones (Season + Bias)?
- → Acceptable, but bias not confirmed yet
- → **VERDICT:** Medium quality, wait or inspect carefully

**RED signal?**
- ❌ Season and Wind don't match?
- ❌ Biases pointing different directions?
- → **VERDICT:** Skip (risk/reward unclear)

### Step 4: Drill Down

1. Click any asset row
2. Navigate to **Asset Story View**
3. See 4H / 1H / 15M charts with zones/levels
4. Confirm deeper structure matches signal

---

## ⏱️ Scan Time Expectations

### Normal Performance

| Setting | Time |
|---------|------|
| **1 asset** | ~10 seconds |
| **3 assets** | ~15–30 seconds |
| **5 assets** | ~30–60 seconds |
| **9 assets** | ~60–90 seconds |

**Per-asset breakdown:**
- Fetch data: ~5–10s
- Validate: <1s
- Run engine: 2–5s
- Render: ~1s
- **Total: ~10–15s per asset** ✓

### When It's Slow

**>15 seconds per asset?**
- ❌ Network slow (check internet)
- ❌ yfinance rate limited (wait 1 minute)
- ❌ Asset data fetch failed (still retrying)

**Timeout protection:** Dashboard will NOT hang >15 seconds per asset (automatic skip)

---

## 🔄 What Happens If Data Loads Fail?

### Scenario A: Asset Fetch Fails

**Error message:** `"XAUUSD load failed: [error]"`

**What it means:** yfinance couldn't get price data

**Reason:** Network issue, symbol delisted, rate limit

**Action:** Asset added to table as invalid (🔴), scanner continues

**User experience:** Transparent—you see exactly why each asset failed

---

### Scenario B: Data Invalid

**Warning:** `"EURUSD data invalid: missing 15M"`

**What it means:** Data returned but missing required timeframe

**Action:** Asset skipped, not added to table

**Reason:** Rare, usually temporary data issue

---

### Scenario C: Incomplete Result

**Warning:** `"No data for GBPUSD; skipping"`

**What it means:** Engine ran but returned partial result

**Action:** Asset skipped silently

**Reason:** Edge case in engine logic (rare)

---

## 💡 Decision Rules

### ✅ Trade Setup Found (GREEN 🟢)

**Conditions:**
- Signal = 🟢 GREEN
- Zone Level ≥ 1 (structural presence)
- R:R ≥ 1:1.3
- Narrative Stage = Deployment

**Next step:** 
1. Click asset → Deep view
2. Confirm on TradingView
3. Take trade

---

### ⚠️ Waiting Setup (ORANGE 🟠)

**Conditions:**
- Signal = 🟠 ORANGE
- Bias not fully aligned
- Can become GREEN if bias confirms

**Next step:**
1. Watch asset
2. If Bias flips, setup becomes GREEN
3. Or wait for more confirmation

---

### ❌ Skip Setup (RED 🔴 or INVALID ⚪)

**Conditions:**
- Signal = 🔴 or ⚪
- Conflicted structure or missing data
- Risk/reward unclear

**Next step:**
- Skip entirely (high risk)
- Or wait for story to clarify
- Don't force a trade here

---

## ⚙️ Scanner Settings

### Max Assets to Scan

**Slider:** 1–9 assets (default 3)

**What it does:** Limits how many assets are processed in one scan

**Guidance:**
- **Start with 3** (fast, focused)
- **Add more if you want wider view** (slower)
- **Don't exceed 9** (performance degrades)

### Refresh

**Button:** "Re-scan all assets"

**What it does:** Restarts scanner from scratch

**When to use:**
- You want fresh data (old data was stale)
- Settings changed
- After a major market move

---

## 🎓 Interpretation Examples

### Example 1: Perfect Alignment

```
Asset:            XAUUSD
Season (4H):      🟢 Upside
Bias (4H):        ↑ Up
Wind (1H):        🟢 Upside
Bias (1H):        ↑ Up
Stage:            Deployment (3)
Signal:           🟢 GREEN
```

**Interpretation:**
- ✅ 4H bullish, expecting higher
- ✅ 1H confirming, also bullish
- ✅ Stage ready for deployment
- ✅ All signals aligned

**Decision:** HIGH QUALITY → Inspect deeper

---

### Example 2: Mixed Signals

```
Asset:            EURUSD
Season (4H):      🟢 Upside
Bias (4H):        → Range
Wind (1H):        🟢 Upside
Bias (1H):        ↑ Up
Stage:            Trend (1)
Signal:           🟠 ORANGE
```

**Interpretation:**
- ⚠️ 4H structure bullish but bias unclear (Range)
- ⚠️ 1H momentum aligns but 4H bias doesn't
- ⚠️ 2/3 conditions aligned only

**Decision:** MEDIUM QUALITY → Wait for 4H bias to confirm

---

### Example 3: Conflicted

```
Asset:            GBPUSD
Season (4H):      🟢 Upside
Bias (4H):        ↓ Down
Wind (1H):        🔴 Downside
Bias (1H):        ↓ Down
Stage:            Retracement (2)
Signal:           🔴 RED
```

**Interpretation:**
- ❌ 4H structure vs. 4H bias conflicted (Up vs Down)
- ❌ 1H pulling back against 4H
- ❌ Only 1/3 aligned (Season)
- ❌ Retracement stage (not deployment)

**Decision:** AVOID → Too conflicted, unclear risk/reward

---

## 🛠️ Troubleshooting

### Q: Signal won't update?
**A:** Refresh page. Signal updates once per scan.

### Q: One asset always fails?
**A:** Symbol may be delisted or data unavailable. Remove from scan or contact support.

### Q: Scanner freezes?
**A:** Should auto-timeout at 15s. If not, refresh page.

### Q: Why is an asset marked INVALID?
**A:** Missing zone, missing R:R, or incomplete structure. Check Weekly Log for details.

---

## 📋 Scanner Workflow Checklist

- [ ] Open Dashboard
- [ ] Set "Max assets to scan" (default 3)
- [ ] Wait for scan to complete
- [ ] Look at Signal column
- [ ] Find 🟢 GREEN signals
- [ ] Verify Signal matches your trade style (if any)
- [ ] Click GREEN signal asset
- [ ] Confirm deeper in Asset Story View
- [ ] Verify on TradingView
- [ ] Execute (or skip if confirmation fails)

---

**Next:** [← Back to Dashboard Guide](00_DASHBOARD_GUIDE.md) | [→ Data Loading Logic](02_DATA_LOADING_LOGIC.md)

