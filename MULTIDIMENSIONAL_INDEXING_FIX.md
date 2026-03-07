# Multi-Dimensional Indexing Error Fix

## Problem Identified

**Error:** `ValueError: Multi-dimensional indexing (e.g. obj[:, None]) is no longer supported`

**Root Cause:**
- `detect_swing_highs()` and `detect_swing_lows()` return **boolean Series** (True/False for each bar)
- We were trying to iterate through the boolean Series as if it were a list of indices
- Pandas 2.0+ no longer allows this multi-dimensional indexing

## Solution Applied

**File:** `visualization/data_provider.py`

Convert boolean Series to list of indices before using:

```python
# BEFORE (broken):
swing_highs_idx = detect_swing_highs(df)  # Returns boolean Series
highs = [(idx[i], float(df["high"].iloc[i])) for i in swing_highs_idx]  # ❌ Error!

# AFTER (fixed):
swing_highs_bool = detect_swing_highs(df)  # Returns boolean Series
swing_highs_idx = [i for i, v in enumerate(swing_highs_bool) if v]  # ✅ Convert to list of indices
highs = [(idx[i], float(df["high"].iloc[i])) for i in swing_highs_idx]  # ✅ Works!
```

### Changes Made

1. **`get_swing_points()`** function:
   - Convert `swing_highs_bool` to `swing_highs_idx` using enumerate + filter
   - Convert `swing_lows_bool` to `swing_lows_idx` using enumerate + filter

2. **`get_blocking_levels()`** function:
   - Same fix applied for consistency

## How It Works

```python
swing_highs_bool = detect_swing_highs(df)  # pd.Series([False, True, False, True, ...])
swing_highs_idx = [i for i, v in enumerate(swing_highs_bool) if v]  # [1, 3, ...]
```

Now we can safely iterate through indices to get the actual values from the dataframe.

## Status

✅ **Fix Applied**  
✅ **Visualization data provider updated**  
✅ **Ready for testing**

Try running the app now:

```bash
streamlit run app.py
```

The chart rendering error should be resolved!
