# KeyError Fix – Column Name Normalization

## Problem Identified

**Error:** `KeyError: "High"` when running the dashboard

**Root Cause:** 
- yfinance returns lowercase column names: `open`, `high`, `low`, `close`
- Engine expects uppercase column names: `Open`, `High`, `Low`, `Close`
- When engine tried to access `df["High"]`, it failed with KeyError

## Solution Implemented

Added automatic column name normalization throughout the engine to handle both uppercase and lowercase column names.

### Files Modified

1. **`engine/structure.py`**
   - Added `_normalize_columns()` function
   - Applied normalization to:
     - `detect_swing_highs()`
     - `detect_swing_lows()`
     - `get_last_confirmed_swing_high()`
     - `get_last_confirmed_swing_low()`
     - `is_structure_break_up()`
     - `is_structure_break_down()`

2. **`engine/narrative.py`**
   - Imported `_normalize_columns` from structure
   - Apply normalization at the start of `run_narrative_engine()`
   - Ensures all input dataframes use uppercase columns before processing

3. **`engine/market_stage.py`**
   - Imported `_normalize_columns` from structure
   - Applied normalization to:
     - `_retracement_ratio_at()`

4. **`engine/zone.py`**
   - Imported `_normalize_columns` from structure
   - Applied normalization to:
     - `_atr_or_range()`
     - `is_not_fully_retraced()`
     - `is_level2_zone_up()`
     - `is_level2_zone_down()`

5. **`engine/fib_logic.py`**
   - Imported `_normalize_columns` from structure
   - Applied normalization to:
     - `zone_dominant_boundary_price()`

## How It Works

```python
def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to uppercase (Open, High, Low, Close) for engine compatibility."""
    if df is None or df.empty:
        return df
    # Create mapping: lowercase/mixed case → uppercase
    m = {}
    for c in df.columns:
        c_lower = c.lower()
        if c_lower == "open":
            m[c] = "Open"
        elif c_lower == "high":
            m[c] = "High"
        elif c_lower == "low":
            m[c] = "Low"
        elif c_lower == "close":
            m[c] = "Close"
    return df.rename(columns=m) if m else df
```

When a dataframe with lowercase columns enters a function:
1. `_normalize_columns()` detects lowercase column names
2. Creates a mapping to uppercase equivalents
3. Returns dataframe with uppercase columns
4. Rest of the function works normally

## Benefits

✅ **Backward Compatible**
- Still works with uppercase column names
- Also handles lowercase (yfinance) and mixed case

✅ **Transparent**
- Automatic normalization in each function
- No breaking changes to API

✅ **Robust**
- Handles multiple column name formats
- Returns unchanged dataframe if no mapping needed

## Testing

The fix has been applied to all engine modules. When you run:

```bash
streamlit run app.py
```

The app will:
1. Fetch data from yfinance (lowercase columns: `open`, `high`, `low`, `close`)
2. Engine automatically normalizes to uppercase
3. All structural, zone, and fib calculations work correctly
4. Dashboard renders candlesticks properly

## Status

✅ **Fix Applied**  
✅ **All engine modules updated**  
✅ **Ready for testing**

Try running the app now - it should work without KeyError!

```bash
streamlit run app.py
```

If you still see errors, they will be different from the KeyError - let me know what the new error is.
