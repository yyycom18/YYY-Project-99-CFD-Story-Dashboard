# CFD Story Dashboard

Narrative Coach Engine v1 — a **narrative state engine** that reflects structural market flow (like a discretionary trader’s reading process). This is **not** a scoring dashboard.

## Rules (strict)

- **Raw data separation:** Engine receives raw UTC data only. No timezone conversion before scoring/structure detection. Visualization uses a converted HKT copy.
- **Timezone:** Engine uses raw timestamps; weekly table display uses Asia/Hong_Kong only.
- **Direction labels:** Use `BIAS_LONG` / `BIAS_SHORT` only; never generic "BIAS".
- **No fallback condition logic:** All condition logic is explicit.

## Target assets

XAUUSD, GBPUSD, EURUSD, USDCAD, NZDUSD, AUDUSD, USDCHF, USDJPY, HK50.

## Timeframes

4H, 1H, 15M (deployment trigger level).

## Run

```bash
cd YYY-Project-99-CFD-Story-Dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Data

- Place OHLC CSV under `data/raw/{ASSET}_{TF}.csv` (e.g. `XAUUSD_15M.csv`) with columns: Open, High, Low, Close; index = datetime.
- If no CSV is found, sample data is generated for development.

## Structure

- `app.py` — Streamlit app; raw → engine, viz = HKT copy.
- `engine/` — market_stage, structure, zone, fib_logic, narrative (no viz).
- `ui/` — charts (4H/1H/15M, stage background, zones), weekly opportunity table.
- `data/fetch.py` — load or generate OHLC (UTC).
- `utils/timezone.py` — convert to HKT for display only.

## Phase 2

Replay Mode (step 15M candle-by-candle, narrative recalculated each step, opportunity log stored) and backtest metrics.
