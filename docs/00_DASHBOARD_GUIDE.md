# 📘 CFD Story Dashboard — User Guide

**Version:** 1.0  
**Last Updated:** 2026-03-11

---

## 🎯 What Is This Dashboard?

The **CFD Story Dashboard** is a **Narrative Market Monitor** designed to help you understand market structure and context.

### Purpose

This dashboard answers: **"Where is the market story right now?"**

It does NOT:
- ❌ Generate trading signals
- ❌ Automate trades
- ❌ Predict price movements

It DOES:
- ✅ Explain market structure (4H Season, 1H Wind, 15M Deployment)
- ✅ Show alignment between timeframes
- ✅ Display zones and key levels
- ✅ Track narrative stages (Environment → Deployment → Resolution)

---

## 🤔 What Problem Does It Solve?

### The Problem

Traders often face:
- **Timeframe confusion:** 4H bullish but 1H bearish → What do I do?
- **Structure uncertainty:** Is this a real break or a fake-out?
- **Level clarity:** Where are the real zones vs. noise?
- **Narrative coherence:** What's the market actually doing?

### The Solution

This dashboard provides a **structured narrative view** where:
- ✅ Each timeframe has a clear role (4H = context, 1H = timing, 15M = execution)
- ✅ Alignment is visible at a glance (🟢 = aligned, 🔴 = conflicted)
- ✅ Zones are clearly marked (Level 1 = momentum, Level 2 = structural)
- ✅ Story progression is transparent (you see the "why" of each stage)

---

## 📊 Dashboard Sections

### 1. **Market Scanner** (Landing Page)

**What it shows:**
Table of all monitored assets with quick-glance status.

**Columns:**
- **Asset** — Currency pair or index (XAUUSD, EURUSD, etc.)
- **Market Regime** — Overall direction (Upside / Downside / Range)
- **Season (4H)** — Higher timeframe direction (context)
- **Bias (4H)** — 4H directional expectation
- **Wind (1H)** — Short-term momentum
- **Bias (1H)** — 1H directional expectation
- **Stage** — Narrative phase (Environment / Trend / Deployment)
- **Signal** — Alignment status (🟢 / 🟠 / 🔴 / ⚪)

**How to use:**
1. Look at **Signal** column
2. 🟢 GREEN? → Story is aligned; inspect deeper
3. 🔴 RED? → Story conflicted; skip or wait
4. Click asset → Deep Structure View

### 2. **Asset Story View** (Detailed Analysis)

**What it shows:**
- 4H / 1H / 15M charts with overlays
- Zone levels and boundaries
- R:R geometry
- Weekly opportunity log

**How to use:**
1. Confirm story alignment (4H + 1H + Bias)
2. Check zone levels (are they structural?)
3. Review R:R (does it meet 1:1.3 minimum?)
4. Check Weekly Log (is this a new or existing opportunity?)

### 3. **Dashboard Guide** (This Page)

**What it shows:**
System documentation and explanations.

---

## 🟢 Understanding the Dashboard

### Signal Lights (Decision Framework)

#### 🟢 GREEN — ALIGNED

**Meaning:** All three conditions point same direction
- 4H Season = Upside ✅
- 1H Wind = Upside ✅
- 4H Bias = Up ✅

**Interpretation:** "Story is coherent"  
**Action:** Watch for deployment opportunity (check 15M charts)

---

#### 🟠 ORANGE — PARTIAL

**Meaning:** Two conditions aligned, one differs
- 4H Season = Upside ✅
- 1H Wind = Upside ✅
- 4H Bias = Range ⚠️

**Interpretation:** "Story is mixed"  
**Action:** Wait for clarity or use caution (bias not confirmed)

---

#### 🔴 RED — UNALIGNED

**Meaning:** Conditions conflicted or opposing
- 4H Season = Upside ✅
- 1H Wind = Downside ❌
- 4H Bias = Down ❌

**Interpretation:** "Story is conflicted"  
**Action:** Don't trade until alignment improves (risk/reward unclear)

---

#### ⚪ INVALID

**Meaning:** Can't assess (missing data)

**Reasons:**
- No structural confirmation (Zone Level = 0)
- No valid R:R geometry
- Narrative incomplete

**Interpretation:** "Insufficient information"  
**Action:** Check why data is missing; skip asset

---

### Market State Definitions

#### 4H Season (Higher Timeframe Context)

**Upside (↑)**
- Structure: Higher highs and higher lows
- Meaning: "Longer-term context is bullish"

**Downside (↓)**
- Structure: Lower highs and lower lows
- Meaning: "Longer-term context is bearish"

**Neutral**
- Structure: Ranging (no confirmed direction)
- Meaning: "No clear higher-timeframe bias"

---

#### 1H Wind (Short-Term Momentum)

**Same scale as 4H Season, but:**
- Follows 4H unless retracement > 68%
- Can flip independently if structure breaks
- Represents "current momentum direction"

---

#### Narrative Stage

| Stage | Meaning | Duration |
|-------|---------|----------|
| **0 — Environment** | Market forming structure, no trend yet | Variable |
| **1 — Trend** | Confirmed directional bias, structure holding | Hours–Days |
| **2 — Retracement** | Pullback within trend (0.5–0.618) | Hours–Minutes |
| **3 — Deployment** | Setup valid, R:R favorable, entry zone active | Minutes–Hours |
| **4 — Liquidity Event** | Institutional activity, zone break/sweep | Minutes |
| **5 — Resolution** | Trade complete, new structure forming | Variable |

---

#### Bias (NOT the same as Stage)

**Bias = Directional Expectation (decision layer)**

**NOT = Current structure (that's Season/Wind)**

- **↑ Up Bias:** Expecting higher prices
- **↓ Down Bias:** Expecting lower prices
- **→ Range Bias:** No confirmed directional edge

**Example:**
- 4H Season = Upside (structure), Bias = Range (expectation)
- → Market is structurally bullish but we don't expect immediate higher prices
- → Wait for 1H confirmation or structure break

---

## 📊 Zone System Explained

### Level 1 — Momentum Zone

**Definition:**
- Large-body candle (body > 1.8x average)
- Small wick (< 30% of body)
- Shows institutional participation

**What it means:** "Institutions were active here"

**Trading relevance:** Weak; can be tested easily

---

### Level 2 — Structural Break Zone

**Definition:**
- Level 1 + structural confirmation (close beyond swing)
- Not fully retraced within next 5 bars
- Body size > 1.5x average

**What it means:** "Institutions acted AND market confirmed (didn't reverse)"

**Trading relevance:** Strong; represents key support/resistance

---

### Zone-Dominant Boundary

**Special rule:**
If Level 2 zone exists between 0.5–0.618 retracement range:
- Zone start becomes the boundary (overrides 0.618 Fib)
- Stronger psychological level

**Example:**
- Retracement range: 100 to 120
- Normal boundary: 120 - (120-100) × 0.618 = 110.76
- Level 2 zone exists at: 111 (institutional activity zone)
- → Use 111 as boundary (more relevant than 110.76)

---

## 💰 R:R System

### What Is R:R?

**R:R = Risk:Reward Ratio**

```
Entry = Current close
Stop = Boundary (structure invalidation level)
Target = Last confirmed swing high/low

Risk = |Entry - Stop|
Reward = |Target - Entry|

R:R = Reward / Risk
```

### Minimum Valid R:R

**Requirement: R:R ≥ 1:1.3**

- Below 1:1.3 → Risk exceeds reward (don't log opportunity)
- 1:1.3–1:1.5 → Acceptable
- 1:1.5–1:2.0 → Good
- Above 1:2.0 → Excellent

---

## 🔄 Weekly Opportunity Log

### What It Shows

Recent deployments logged in last 4 weeks:
- Date / Time (HKT)
- Asset and Timeframe
- Narrative Stage at entry
- Zone Level and Boundary
- R:R achieved
- Deployment Trigger (Yes/No)
- Result (if completed)

### How to Use

1. **New opportunities:** Check if setup is new or already logged
2. **Learning:** Review past wins/losses, identify patterns
3. **Bias check:** Did outcome match directional bias?

---

## ⚙️ System Settings

### Market Scanner

**Max Assets to Scan:** 1–9 (default 3)

**Guidance:**
- 1–3 assets: Fast (~15 seconds)
- 4–6 assets: Medium (~60 seconds)
- 7–9 assets: Slow (>60 seconds)

### Lookback Days

**For asset detail view:** 5–60 days (default 14)

**Higher = more history, slower rendering**

---

## 🎓 Basic Workflow

### Step 1: Scan Assets

1. Go to **Market Scanner** tab
2. Set "Max assets to scan" (start with 3)
3. Review signal lights
4. Look for 🟢 GREEN or 🟠 ORANGE

### Step 2: Inspect Deeper

1. Click asset with green/orange signal
2. Review 4H / 1H / 15M charts
3. Check zone levels and boundaries
4. Confirm R:R meets 1:1.3 minimum

### Step 3: Check Weekly Log

1. See if this is a new opportunity
2. Review past outcomes (bias accuracy?)
3. Decide: Trade now or wait for confirmation?

### Step 4: Verify on TradingView

1. Open asset on TradingView
2. Confirm zones and levels visually
3. Check for institutional activity nearby
4. Make final decision (trade or pass)

---

## 🛑 When NOT to Trade

- ❌ Signal is 🔴 RED (conflicted story)
- ❌ Zone Level = 0 (no structural confirmation)
- ❌ R:R < 1:1.3 (risk exceeds reward)
- ❌ Weekly Log shows same setup failed last time
- ❌ You feel uncertain (this dashboard is for clarity, not guessing)

---

## ✅ Key Takeaways

1. **This dashboard shows CONTEXT, not signals**
2. **Signal light (🟢/🟠/🔴) = alignment check**
3. **Zones matter (Level 2 > Level 1)**
4. **R:R matters (minimum 1:1.3)**
5. **Weekly log tracks history**
6. **Always confirm on TradingView before trading**

---

## 📞 Questions?

### Common Questions

**Q: Why does the scanner sometimes show N/A for Bias?**  
A: Data not yet computed (rare). Refresh or check data source.

**Q: Can I trade 🟠 ORANGE signals?**  
A: Possible but riskier. Bias not confirmed yet; wait for clarity.

**Q: What if Zone Level = 0?**  
A: No structural confirmation yet. Market still forming. Skip.

**Q: Why does signal change?**  
A: Market evolves. Stage, zone, or bias changes → alignment changes.

### Report Issues

If dashboard freezes, shows errors, or has missing data:
1. Refresh page (`Cmd/Ctrl + R`)
2. Check sidebar for error messages
3. Contact dashboard support

---

**Last Section — See other guides for technical details.**

