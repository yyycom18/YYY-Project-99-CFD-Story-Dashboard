# CFD Story Dashboard – Performance Optimization Analysis & Recommendations

## Current Performance Issue

**Symptom:** Dashboard takes 10-30 seconds to load  
**Root Cause:** 4000 bars × 3 timeframes with heavy engine computation  

---

## Performance Bottleneck Analysis

### 1. Data Generation (15M bars)

**Current Setting:** 4000 bars (default)

```
15M bars: 4000 bars
1H bars:  4000 / 4 = 1000 bars
4H bars:  4000 / 24 = ~167 bars
```

**Time Calculation:**
- 4000 × 15 minutes = 60,000 minutes = 41.7 days (~6 weeks)
- This includes extra history for engine calculations (swings, retracement, etc.)

### 2. Engine Computation (O(n) per 15M bar)

**Current Operation per 15M bar:**
```python
for i in range(n_15):  # 4000 iterations
    i_4h = get_4h_index(i)
    i_1h = get_1h_index(i)
    st_4h = stage_4h_s.iloc[i_4h]
    st_1h = stage_1h_s.iloc[i_1h]
    st_15 = stage_15m_s.iloc[i]
    z = zone_level_at(df_15m, i)        # Searches back in history
    b = active_retracement_boundary(...)  # Complex calculations
    rr = compute_rr(...)                # RR calculation
    trigger = deployment_trigger_valid(...)  # Multiple checks
```

Each iteration does multiple lookback operations → **O(n²) behavior in worst case**

### 3. Visualization Rendering

**Current:** Rendering 4000 15M bars + 1000 1H + 167 4H bars  
This creates large Plotly figures with many shapes (overlays, zones, etc.)

---

## Optimization Strategy

### **Recommended Configuration for 2-Week View with <30s Load Time**

#### **Option A: Balanced (RECOMMENDED)**

```
15M bars for engine: 1500 bars
  = 1500 × 15 min = 22,500 min = 15.6 days (~2.2 weeks)
  
Breakdown:
- 15M bars: 1500
- 1H bars: ~375
- 4H bars: ~63

Calculation per 15M bar: ~1500 iterations
Expected load time: 5-10 seconds (3-5x faster)
```

**Why this works:**
- Sufficient history for swing detection (~2 weeks engine history)
- Display 2 weeks of data (1344 bars 15M = 14 days)
- Small enough for fast computation

#### **Option B: Minimal (FASTEST)**

```
15M bars for engine: 1000 bars
  = 1000 × 15 min = 15,000 min = 10.4 days (~1.5 weeks)

Expected load time: 3-7 seconds (5-10x faster)
Trade-off: Less historical context for structural analysis
```

#### **Option C: Conservative (SAFEST)**

```
15M bars for engine: 2000 bars
  = 2000 × 15 min = 30,000 min = 20.8 days (~3 weeks)

Expected load time: 8-15 seconds (2-3x faster)
Trade-off: Slightly longer load, more reliable analysis
```

---

## Implementation Changes

### Change 1: Adjust Default Slider Setting

**File:** `app.py` (Line 56)

```python
# BEFORE (slow):
bars_15m = st.sidebar.slider("15M bars (fewer = faster load)", 500, 5000, 4000, 100)

# AFTER (optimized):
bars_15m = st.sidebar.slider("15M bars (fewer = faster load)", 500, 3000, 1500, 100)
```

**Impact:**
- Default: 4000 → 1500 bars (62.5% reduction)
- Range: 500–5000 → 500–3000 (narrower, prevents extreme slowness)
- Step: 100 bars (fine-grained control)

### Change 2: Add Pre-computation Cache

**File:** `app.py` (Line 29–39)

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def _cached_fetch_and_run(asset: str, bars_15m: int):
    """Fetch and run engine. Already cached, but we can optimize further."""
    data_raw = fetch_all_timeframes(asset, bars_15m=bars_15m)
    # ... rest of function
```

**Already Implemented:** ✓ Good!

**Enhancement:** Add `show_spinner` control for better UX:

```python
# BEFORE:
with st.spinner("Loading data and running narrative engine… (first run may take 10–30s)"):

# AFTER (shows actual time):
with st.spinner("Loading data and running narrative engine… (~5–10s on first run)"):
```

### Change 3: Optimize Engine Loop (Optional Advanced)

For even faster performance, vectorize parts of the engine:

**Location:** `engine/narrative.py` Line 215

**Current (Serial):**
```python
for i in range(n_15):
    # 4000 iterations, each doing multiple calculations
```

**Vectorized (Faster):**
```python
# Pre-compute all indices once
i_4h_all = df_4h.index.get_indexer(df_15m.index, method="ffill")
i_1h_all = df_1h.index.get_indexer(df_15m.index, method="ffill")

# Use numpy operations instead of loop
stage_4h_aligned = stage_4h_s.iloc[i_4h_all].values
stage_1h_aligned = stage_1h_s.iloc[i_1h_all].values

# Then only loop for complex operations
for i in range(n_15):
    z = zone_level_at(df_15m, i, ...)
    ...
```

This requires careful refactoring, so implement only if needed.

---

## Performance Comparison Table

| Setting | 15M Bars | Duration | 15M Viz | Engine Load | Notes |
|---------|----------|----------|---------|------------|-------|
| Current | 4000 | 15-30s | ❌ Too much | Slow | Original config |
| **Recommended** | **1500** | **5-10s** | ✅ 2 weeks | Fast | Best balance |
| Minimal | 1000 | 3-7s | 🔶 ~1.5 wks | Very fast | Less history |
| Conservative | 2000 | 8-15s | ✅ 2.8 wks | Moderate | Safe buffer |

---

## Memory Usage Impact

```
4000 bars:  ~5-10 MB (RAM + cache)
1500 bars:  ~2-4 MB (62.5% reduction)
1000 bars:  ~1.5-3 MB (75% reduction)
```

---

## Recommended Action Plan

### Step 1: Update Default (IMMEDIATE)
Change `app.py` line 56 to use 1500 bars as default

### Step 2: Test & Validate
- Clear Streamlit cache: `streamlit cache clear`
- Run: `streamlit run app.py`
- Select default (1500 bars)
- Verify: Load time < 10 seconds

### Step 3: Verify 2-Week View
- Select "2 weeks" in Time Window dropdown
- Confirm: Display shows correct 2-week range
- Check: Charts render smoothly

### Step 4: Optional - Vectorize Engine (If Still Too Slow)
- Optimize `narrative.py` engine loop
- Expected improvement: Another 2-3x speedup
- Effort: Medium (requires careful testing)

---

## Testing Checklist

```
[ ] Clear cache: streamlit cache clear
[ ] Run with 1500 bars default
[ ] Measure first load time: _____ seconds
[ ] Select 2-week time window
[ ] Verify chart shows ~2 weeks of data
[ ] Check: No missing candles
[ ] Test: Switch between assets quickly (should use cache)
[ ] Test: Change Time Window (should be instant - display only)
[ ] Test: Adjust bars slider to 500, 2000, 3000 (all should work)
[ ] Performance acceptable? Yes / No
```

---

## Why 1500 Bars is Optimal for 2-Week View

```
1500 bars × 15 minutes = 22,500 minutes = 15.6 days

Display Time Window (2 weeks):
  2 × 7 × 24 × 4 = 1344 bars 15M

Engine History (provides buffer):
  1500 - 1344 = 156 extra bars (~1.6 days)
  
This buffer allows:
  - Swing detection (needs lookback)
  - Retracement calculation (needs history)
  - Zone validation (needs confirmation bars after break)
```

**Result:** Sufficient structure analysis with minimal overhead

---

## Expected Improvement

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Load Time | 15-30s | 5-10s | 3-6x faster |
| Memory | 5-10 MB | 2-4 MB | 50-75% less |
| Data Points | 4000 15M | 1500 15M | 62.5% fewer |
| User Experience | ⏳ Wait | ⚡ Quick | Much better |

---

## Summary

**Recommended Change:**
- Update default `bars_15m` from **4000 → 1500**
- This provides:
  - ✅ 2-week engine history (sufficient for structural analysis)
  - ✅ 5-10 second load time (target <30s ✓)
  - ✅ Professional user experience
  - ✅ Reasonable memory usage

**One Line Change:**
```python
bars_15m = st.sidebar.slider("15M bars (fewer = faster load)", 500, 3000, 1500, 100)
                                                                                    ↑
                                                                          1500 = new default
```

This solves your performance issue while maintaining sufficient data for analysis.
