# Trading Strategy Summary Dashboard (Python + Dash)

This is a **local**, interactive dashboard that renders:
- Equity curve (with high-water mark)
- Drawdown curve (with high-water mark on a secondary axis)
- A hover-to-explain metrics table (Sharpe, Sortino, Calmar, max drawdown, hit rate, profit factor, etc.)
- A "Custom Analytics" panel (Correlation / Rolling Sharpe / Seasonality)

It also supports:
- **Strategy selection** via a top-left button that opens a sidebar
- **Product selection** via the top bar (includes an **All** option)

## 1) Put the CSVs in the `data/` folder

Copy your CSV files into this folder:
- `momentum_pnls.csv`
- `mean_reversion_pnls.csv`
- `carry_pnls.csv`
- `machine_learning_pnls.csv`
- `short_strangle_pnls.csv`
- `intraweek_seasonality_pnls.csv`

(They should have a date column such as `Unnamed: 0` or `date`, and product columns like `brent`, `gasoil`, `fuel_oil`.)

## 2) Install dependencies

### Windows (PowerShell)
```powershell
cd trading_strategy_dashboard_py
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux
```bash
cd trading_strategy_dashboard_py
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) Run
```bash
python app.py
```

Then open: `http://127.0.0.1:8050`

## Notes / Extension points
- Add more strategies in `load_strategies()` (read more CSVs).
- Add more custom analytics tabs in `Custom Analytics`.
- If you prefer PnL to be treated as % returns, we can add a toggle and change aggregation logic.
