# CFD Story Dashboard – Alignment to Golden Source

## Key Differences Identified

### 1. Data Sourcing
**Golden Source:** Uses `yfinance` to fetch real market data
**Current Project:** Uses synthetic generated data

**Impact:** Real data from yfinance has accurate OHLC relationships, causing perfect candlestick alignment

### 2. Data Structure
**Golden Source:** Column names: `open`, `high`, `low`, `close` (lowercase)
**Current Project:** Column names: `Open`, `High`, `Low`, `Close` (mixed case)

### 3. Chart Building
**Golden Source:** Modular approach with:
- `market_data.py` → Fetch real data via yfinance
- `data_provider.py` → Compute visualization overlays
- `layout.py` → Build figure using modular plot functions
- `plot_trend.py`, `plot_structure.py`, `plot_deployment.py` → Individual chart builders

**Current Project:** Monolithic `charts.py` with everything in one file

### 4. Symbol Mapping
**Golden Source:** Maps user-friendly names to Yahoo Finance symbols
```python
SYMBOL_MAP = {
    "XAUUSD": "GC=F",      # Commodity futures
    "EURUSD": "EURUSD=X",  # Forex pairs
    "AUDUSD": "AUDUSD=X",
    "HK50": "^HSI",        # Index
}
```

## Alignment Plan

### Phase 1: Implement Real Data Sourcing
✅ Replace synthetic data generator with `yfinance` integration
✅ Add symbol mapping for all assets
✅ Maintain UTC timezone handling

### Phase 2: Restructure Data Files
✅ Create `visualization/market_data.py` with yfinance fetcher
✅ Update `data/fetch.py` to use yfinance instead of synthetic generation
✅ Normalize column names to lowercase

### Phase 3: Modularize Chart Building
✅ Split monolithic `ui/charts.py` into:
  - `visualization/data_provider.py` (overlay computation)
  - `visualization/layout.py` (figure building)
  - `visualization/plot_trend.py` (4H chart)
  - `visualization/plot_structure.py` (1H chart)
  - `visualization/plot_deployment.py` (15M chart)
  - `visualization/overlays.py` (helper functions)

### Phase 4: Update App Integration
✅ Update `app.py` to use new data sourcing
✅ Integrate modular chart builders

## Implementation Steps

This alignment will provide:
- ✅ Real market data (accurate OHLC)
- ✅ Professional candlestick rendering
- ✅ Exact match to golden source appearance
- ✅ Better code organization
- ✅ Easier maintenance and debugging

**Expected Result:** Dashboard candlesticks will match golden source perfectly!
