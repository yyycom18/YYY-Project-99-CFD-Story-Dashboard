# 🎯 Signal & Bias Explained

**Quick Navigation:** [← Back to Dashboard Guide](00_DASHBOARD_GUIDE.md)

---

## Core Concepts

The dashboard uses three core concepts to describe market state:

1. **4H Season** — Higher timeframe direction (context)
2. **1H Wind** — Short-term momentum (timing)
3. **Bias** — Directional expectation (decision layer)

⚠️ **Critical:** These are NOT the same thing

---

## 🏔️ 4H Season (Higher Timeframe Context)

### What It Represents

The **established direction** on the 4-hour timeframe.

"Is the market in an uptrend, downtrend, or ranging?"

### Values

#### 🟢 Upside
**Definition:** Higher highs AND higher lows

**Example:**
```
Swing High: 1.1500 → 1.1520 → 1.1550 ✅ (higher)
Swing Low:  1.1450 → 1.1480 → 1.1510 ✅ (higher)
→ Upside confirmed
```

**Market interpretation:** Bullish structural bias

**Action:** Watch for continuation or reversal

---

#### 🔴 Downside
**Definition:** Lower highs AND lower lows

**Example:**
```
Swing High: 1.1550 → 1.1520 → 1.1490 ✅ (lower)
Swing Low:  1.1510 → 1.1480 → 1.1450 ✅ (lower)
→ Downside confirmed
```

**Market interpretation:** Bearish structural bias

---

#### ⚪ Neutral
**Definition:** Range (no clear directional structure)

**Example:**
```
Swing High: 1.1500 → 1.1510 → 1.1505 ❌ (ranging)
Swing Low:  1.1450 → 1.1455 → 1.1460 ❌ (ranging)
→ No directional bias
```

**Market interpretation:** Waiting for break

---

### How 4H Season Is Calculated

```
Look at: Last 50–100 bars on 4H chart
Find: Swing highs and swing lows
Count: How many HH/HL or LL/LH?
→ More HH/HL = Upside
→ More LL/LH = Downside
→ Mixed = Neutral
```

---

## 💨 1H Wind (Short-Term Momentum)

### What It Represents

The **current momentum direction** on 1-hour timeframe.

"Is short-term moving WITH or AGAINST 4H?"

### Values

**Same as 4H Season:**
- 🟢 Upside (1H bullish)
- 🔴 Downside (1H bearish)
- ⚪ Neutral (1H ranging)

### Key Difference from 4H

**1H Wind CAN differ from 4H Season**

**Example:**
```
4H Season: 🟢 Upside (bullish context)
1H Wind:   🔴 Downside (pullback in progress)

Interpretation:
→ Market is bullish but currently pulling back
→ Expect bounce back to upside after retracement
```

### When Does 1H Flip?

**Rule:** 1H only flips if retracement > 68%

**Example:**
```
Scenario A: Retracement = 50%
4H: Upside, 1H: Upside ✅ (continues)

Scenario B: Retracement = 75%
4H: Upside, 1H: Downside ⚠️ (could flip)

If not retraced back: 1H becomes Downside
If retraced back: 1H returns to Upside
```

---

## 🎲 Bias (Directional Expectation)

### What It Represents

Your **directional edge** or **trading expectation**.

**Key:** Bias is NOT the current structure—it's your expectation

---

### Values

#### ↑ Up Bias
**Meaning:** Expecting prices to go higher

**Basis:**
- Could be based on 4H uptrend
- Could be based on zone support
- Could be based on wave structure
- **Not just "price is going up now"**

**Example:**
```
Situation: 4H Upside, but price in retracement
Bias: ↑ Up (expecting bounce back up)
Action: Watch for reversal from support zone
```

---

#### ↓ Down Bias
**Meaning:** Expecting prices to go lower

**Basis:**
- 4H downtrend, or
- Zone resistance ahead, or
- Wave structure suggests lower

---

#### → Range Bias
**Meaning:** No confirmed directional edge

**Basis:**
- Could go either way
- Structure unclear
- Waiting for confirmation

---

### Critical: Bias ≠ Season/Wind

**WRONG interpretation:**
> "If 4H is Upside, then Bias is Up"

**CORRECT interpretation:**
> "4H Upside is CONTEXT. Bias depends on current setup AND retracement depth AND zone structure."

**Example that shows the difference:**
```
4H Season: 🟢 Upside (structural)
1H Wind:   🟢 Upside (momentum)
Bias:      → Range (expectation?)

Why Range if everything is Up?
Reason: Could be—
  • Deep retracement (-0.70) → no edge yet
  • Zone resistance ahead → trapped
  • No swing confirmation → waiting
```

---

## 🔗 How They Work Together

### The Model

```
4H Season (Context)
    ↓
    What is the larger market doing?
    Is it bullish, bearish, or ranging?
    
    ↓
    
1H Wind (Timing)
    ↓
    Is short-term moving WITH or AGAINST 4H?
    Can we enter on the 4H direction?
    
    ↓
    
Bias (Decision)
    ↓
    Based on Season + Wind + Zone + Structure,
    What is our expectation for NEXT move?
    Where should we expect price to go?
```

---

### Scenario 1: Perfect Alignment

```
4H Season: 🟢 Upside
1H Wind:   🟢 Upside
Bias:      ↑ Up

Interpretation:
✅ 4H context: bullish
✅ 1H momentum: confirming
✅ Expectation: higher prices likely

Decision: HIGH QUALITY SETUP
Action: Watch 15M for entry
```

---

### Scenario 2: 4H Upside, 1H Retracing

```
4H Season: 🟢 Upside
1H Wind:   🔴 Downside (pullback)
Bias:      ↑ Up (expecting bounce)

Interpretation:
✅ 4H context: bullish
⚠️ 1H momentum: temporarily down (normal retracement)
✅ Expectation: Bounce back to upside after pullback

Decision: MEDIUM QUALITY (waiting for bounce)
Action: Watch for reversal from support zone
```

---

### Scenario 3: 4H Upside, 1H Downside, Bias Range

```
4H Season: 🟢 Upside
1H Wind:   🔴 Downside
Bias:      → Range

Interpretation:
✅ 4H context: bullish
⚠️ 1H momentum: bearish (strong pullback)
❌ Expectation: Unclear (retracement too deep?)

Decision: LOW QUALITY (structure unclear)
Action: Wait for structure to clarify
```

---

### Scenario 4: Conflicted

```
4H Season: 🟢 Upside
1H Wind:   🔴 Downside
Bias:      ↓ Down

Interpretation:
✅ 4H context: bullish
❌ 1H momentum: bearish
❌ Expectation: lower prices (conflicts with 4H)

Decision: VERY LOW QUALITY (dangerous)
Action: Skip (risk/reward unclear)
```

---

## 📊 Signal Light System (Based on Alignment)

### How Signal Is Calculated

```
Score = 0
If 4H Season = Upside (+1):     Score += 1
If 1H Wind = Upside (+1):       Score += 1
If Bias = Up (+1):              Score += 1

Result:
Score = 3: 🟢 GREEN (perfect)
Score = 2: 🟠 ORANGE (partial)
Score = 0–1: 🔴 RED (conflicted)
```

---

### 🟢 GREEN Signal Checklist

- [ ] 4H Season = 🟢 Upside
- [ ] 1H Wind = 🟢 Upside
- [ ] Bias = ↑ Up
- [ ] Zone Level ≥ 1 (structural)
- [ ] R:R ≥ 1:1.3
- [ ] Stage = Deployment or Trend

**Verdict:** High quality setup

---

### 🟠 ORANGE Signal Checklist

- [ ] 2 out of 3 are aligned
- [ ] OR 3/3 aligned but R:R < 1:1.3
- [ ] OR Zone Level = 0
- [ ] Missing something but not completely conflicted

**Verdict:** Medium quality (watch for confirmation)

---

### 🔴 RED Signal Checklist

- [ ] 4H Season = 🟢 Upside BUT 1H Wind = 🔴 Downside
- [ ] AND Bias = ↓ Down
- [ ] OR conflicted structure
- [ ] Missing zone or R:R

**Verdict:** Low quality (skip or wait)

---

### ⚪ INVALID Signal

- [ ] Zone Level = 0 (no structure)
- [ ] R:R missing or 0 (no geometry)
- [ ] Narrative Stage missing (incomplete)
- [ ] Cannot make decision due to missing data

**Verdict:** Can't assess (skip)

---

## 🎓 Practical Examples

### Example 1: Learning Setup

```
Asset: XAUUSD
4H Season: 🟢 Upside (HH/HL confirmed)
1H Wind:   🟢 Upside (also HH/HL)
Bias:      ↑ Up (expecting higher)
Signal:    🟢 GREEN

What you see on charts:
- 4H: Clear uptrend, higher highs
- 1H: Also uptrending, confirming 4H
- 15M: Small pullback (normal)
- Zone: Level 2 zone at support

What to do:
1. ✅ Check 15M for entry point
2. ✅ Confirm zone support holds
3. ✅ Enter on break of pullback high
4. ✅ Stop: Below zone
5. ✅ Target: Last swing high
```

---

### Example 2: Caution Setup

```
Asset: EURUSD
4H Season: 🟢 Upside (higher highs)
1H Wind:   🔴 Downside (strong pullback)
Bias:      ↑ Up (expecting bounce)
Signal:    🟠 ORANGE

What you see on charts:
- 4H: Uptrend intact
- 1H: Deep pullback (-72% of upswing)
- 15M: Still going down
- Zone: No zone confirmed yet

What to do:
1. ⚠️ Wait: Is 1H bounce back up? Or break down?
2. ⚠️ If 1H bounces → Setup becomes GREEN
3. ⚠️ If 1H breaks down → Signal changes to RED
4. ⚠️ HOLD: Don't enter until structure clarifies
```

---

### Example 3: Avoid Setup

```
Asset: GBPUSD
4H Season: 🟢 Upside (HH/HL)
1H Wind:   🔴 Downside (LL/LH)
Bias:      ↓ Down (expecting lower!)
Signal:    🔴 RED

What you see on charts:
- 4H: Uptrend but...
- 1H: Breaking into downtrend
- Conflict: 4H says up, 1H says down
- Risk/Reward: Unclear

What to do:
1. ❌ SKIP: Too conflicted
2. ❌ Don't guess which wins
3. ❌ Wait until 4H or 1H resolves
4. ❌ Only enter when alignment clear
```

---

## 💡 Decision Rules

### Rule 1: Green Light Go

```
IF Signal = 🟢 GREEN
  THEN: Check 15M for entry
  THEN: Verify R:R one more time
  THEN: Enter if aligned
```

### Rule 2: Orange Light Wait

```
IF Signal = 🟠 ORANGE
  THEN: Watch for alignment
  THEN: If flips to 🟢, consider entry
  THEN: If flips to 🔴, skip
  THEN: Don't force a trade
```

### Rule 3: Red Light Stop

```
IF Signal = 🔴 RED or ⚪ INVALID
  THEN: Skip this asset
  THEN: Find a 🟢 GREEN instead
  THEN: Only trade when aligned
```

---

## Common Mistakes

### ❌ Mistake 1: Trading on Season Alone

```
WRONG:
"4H is Upside → trade long"

RIGHT:
"4H is Upside AND 1H confirms AND Bias aligned → trade long"
```

### ❌ Mistake 2: Ignoring Retracement Depth

```
WRONG:
"4H up, 1H pulling back 30% → still up"

RIGHT:
"4H up, 1H pulling back 75% → could flip to downside"
```

### ❌ Mistake 3: Trading Without Zone

```
WRONG:
"Signal is green, so enter anywhere"

RIGHT:
"Signal is green AND Zone Level ≥ 1 → enter in zone"
```

### ❌ Mistake 4: Confusing Bias with Season

```
WRONG:
"4H is Upside means Bias is Up"

RIGHT:
"4H Upside means CONTEXT. Bias depends on structure, retracement, and zone."
```

---

## Quick Reference Card

### 4H Season
- **Meaning:** Direction on 4H timeframe
- **Values:** Upside / Downside / Neutral
- **Basis:** Structure (HH/HL or LL/LH)
- **Role:** Context / Reference Frame

### 1H Wind
- **Meaning:** Direction on 1H timeframe
- **Values:** Upside / Downside / Neutral
- **Basis:** Structure (can differ from 4H if retrace > 68%)
- **Role:** Confirmation / Timing

### Bias
- **Meaning:** Your directional expectation
- **Values:** Up / Down / Range
- **Basis:** Season + Wind + Zone + Structure
- **Role:** Decision Layer / Risk Limit

### Signal
- **Meaning:** Alignment of above three
- **Values:** 🟢 / 🟠 / 🔴 / ⚪
- **Basis:** Count if 4H = Up, 1H = Up, Bias = Up
- **Role:** Go/No-Go Decision

---

**Next:** [← Back to Dashboard Guide](00_DASHBOARD_GUIDE.md)

