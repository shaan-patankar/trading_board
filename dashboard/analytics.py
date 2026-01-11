from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from dashboard.config import RANGE_OPTIONS


@dataclass(frozen=True)
class SeriesPack:
    dates: pd.Series
    pnl: pd.Series
    equity: pd.Series
    hwm: pd.Series
    drawdown: pd.Series
    returns: pd.Series


def compute_series(df: pd.DataFrame, products: List[str]) -> SeriesPack:
    dates = df["date"]

    if len(products) == 0:
        pnl = pd.Series(np.zeros(len(df)), index=df.index)
    else:
        pnl = df[products].sum(axis=1)

    equity = pnl.cumsum()
    # hwm = pd.Series(np.maximum.accumulate(np.maximum(equity.to_numpy(), 0.0)), index=equity.index)
    hwm = equity.cummax()

    prev_eq = equity.shift(1).replace(0, np.nan)
    rets = (pnl / prev_eq).fillna(0.0)

    # dd = pd.Series(np.where(hwm.to_numpy() == 0.0, 0.0, (equity / hwm) - 1.0), index=equity.index)
    dd = equity - hwm
    
    return SeriesPack(dates=dates, pnl=pnl, equity=equity, hwm=hwm, drawdown=dd, returns=rets)


def annualize_factor_from_dates(dates: pd.Series) -> int:
    # if len(dates) < 3:
    #     return 252
    # d = pd.to_datetime(dates)
    # deltas = d.diff().dropna().dt.days
    # med = deltas.median()
    # if pd.isna(med):
    #     return 252
    # if med <= 2:
    #     return 252
    # if med <= 8:
    #     return 52
    # return 12
    return 252


def padded_date_range(dates: pd.Series, pad_frac: float = 0.1) -> Optional[Tuple[pd.Timestamp, pd.Timestamp]]:
    valid_dates = pd.to_datetime(dates).dropna()
    if valid_dates.empty:
        return None

    start = valid_dates.min()
    end = valid_dates.max()
    span = end - start
    pad = span * pad_frac if span > pd.Timedelta(0) else pd.Timedelta(days=30)
    return start - pad, end + pad


def filter_df_by_range(df: pd.DataFrame, range_key: Optional[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    range_key = range_key or "All"
    if range_key == "All":
        return df

    dates = pd.to_datetime(df["date"], errors="coerce")
    end = dates.max()
    if pd.isna(end):
        return df

    if range_key == "1M":
        start = end - pd.DateOffset(months=1)
    elif range_key == "3M":
        start = end - pd.DateOffset(months=3)
    elif range_key == "YTD":
        start = pd.Timestamp(end.year, 1, 1)
    elif range_key == "1Y":
        start = end - pd.DateOffset(years=1)
    else:
        return df

    mask = (dates >= start) & (dates <= end)
    filtered = df.loc[mask].copy()
    return filtered if not filtered.empty else df


def next_range_key(current: Optional[str]) -> str:
    current_value = current or "All"
    try:
        idx = RANGE_OPTIONS.index(current_value)
    except ValueError:
        idx = len(RANGE_OPTIONS) - 1
    return RANGE_OPTIONS[(idx + 1) % len(RANGE_OPTIONS)]


def range_cycle_label(*ranges: Optional[str]) -> str:
    normalized = [value or "All" for value in ranges]
    unique = {value for value in normalized}
    if len(unique) == 1:
        return f"All Panels: {normalized[0]}"
    return "All Panels: Mixed"


def compute_metrics(sp: SeriesPack, rf_annual: float = 0.0) -> List[dict]:
    dates = pd.to_datetime(sp.dates)
    ann = annualize_factor_from_dates(dates)

    rets = sp.returns.copy()
    rf_period = (1.0 + rf_annual) ** (1.0 / ann) - 1.0
    ex = rets - rf_period

    eps = 1e-12
    mean_r = float(ex.mean())
    std_r = float(ex.std(ddof=1)) if len(ex) > 1 else 0.0

    downside = ex.where(ex < 0.0, 0.0)
    downside_std = float(np.sqrt((downside**2).mean())) if len(ex) > 0 else 0.0

    sharpe = (mean_r / (std_r + eps)) * math.sqrt(ann) if std_r > 0 else np.nan
    sortino = (mean_r / (downside_std + eps)) * math.sqrt(ann) if downside_std > 0 else np.nan

    max_dd = float(sp.drawdown.min()) if len(sp.drawdown) else np.nan
    total_pnl = float(sp.pnl.sum()) if len(sp.pnl) else 0.0

    init = float(sp.equity.iloc[0] - sp.pnl.iloc[0]) if len(sp.equity) else np.nan
    final_eq = float(sp.equity.iloc[-1]) if len(sp.equity) else np.nan

    if init > 0 and final_eq > 0 and len(dates) > 1:
        years = (dates.iloc[-1] - dates.iloc[0]).days / 365.25
        cagr = (final_eq / init) ** (1.0 / max(years, 1e-9)) - 1.0
    else:
        cagr = np.nan

    calmar = (cagr / abs(max_dd)) if (not np.isnan(cagr) and max_dd < 0) else np.nan

    hit_rate = float((sp.pnl > 0).mean()) if len(sp.pnl) else np.nan
    avg_win = float(sp.pnl[sp.pnl > 0].mean()) if (sp.pnl > 0).any() else np.nan
    avg_loss = float(sp.pnl[sp.pnl < 0].mean()) if (sp.pnl < 0).any() else np.nan

    sum_win = float(sp.pnl[sp.pnl > 0].sum()) if (sp.pnl > 0).any() else 0.0
    sum_loss = float(sp.pnl[sp.pnl < 0].sum()) if (sp.pnl < 0).any() else 0.0
    profit_factor = (sum_win / abs(sum_loss)) if sum_loss < 0 else np.nan

    vol = std_r * math.sqrt(ann) if std_r > 0 else np.nan

    below = (sp.equity < sp.hwm).to_numpy()
    max_dur, cur = 0, 0
    for b in below:
        if b:
            cur += 1
            max_dur = max(max_dur, cur)
        else:
            cur = 0

    expectancy = float(sp.pnl.mean()) if len(sp.pnl) else np.nan

    def fmt_pct(x: float) -> str:
        return "—" if (x is None or np.isnan(x)) else f"{x*100:,.2f}%"

    def fmt_num(x: float) -> str:
        return "—" if (x is None or np.isnan(x)) else f"{x:,.4f}"

    def fmt_cash(x: float) -> str:
        return "—" if (x is None or np.isnan(x)) else f"{x:,.2f}"

    eq_series = pd.Series(sp.equity.values, index=pd.to_datetime(sp.dates))
    monthly_ret = eq_series.resample("M").last().pct_change().dropna()

    rows = [
        {"Metric": "Total PnL", "Value": fmt_cash(total_pnl)},
        {"Metric": "Final Equity", "Value": fmt_cash(final_eq)},
        {"Metric": "CAGR", "Value": fmt_pct(cagr)},
        {"Metric": "Volatility", "Value": fmt_pct(vol)},
        {"Metric": "Sharpe", "Value": fmt_num(sharpe)},
        {"Metric": "Sortino", "Value": fmt_num(sortino)},
        {"Metric": "Max Drawdown", "Value": fmt_pct(max_dd)},
        {"Metric": "Calmar", "Value": fmt_num(calmar)},
        {"Metric": "Hit Rate", "Value": fmt_pct(hit_rate)},
        {"Metric": "Profit Factor", "Value": fmt_num(profit_factor)},
        {"Metric": "Avg Win", "Value": fmt_cash(avg_win)},
        {"Metric": "Avg Loss", "Value": fmt_cash(avg_loss)},
        {"Metric": "Best Day PnL", "Value": fmt_cash(float(sp.pnl.max()) if len(sp.pnl) else np.nan)},
        {"Metric": "Worst Day PnL", "Value": fmt_cash(float(sp.pnl.min()) if len(sp.pnl) else np.nan)},
        {"Metric": "Median Daily PnL", "Value": fmt_cash(float(sp.pnl.median()) if len(sp.pnl) else np.nan)},
        {"Metric": "Std Daily PnL", "Value": fmt_cash(float(sp.pnl.std(ddof=1)) if len(sp.pnl) > 1 else np.nan)},
        {"Metric": "Avg Monthly Return", "Value": fmt_pct(float(monthly_ret.mean()) if len(monthly_ret) else np.nan)},
        {
            "Metric": "Monthly Return Vol",
            "Value": fmt_pct(float(monthly_ret.std(ddof=1)) if len(monthly_ret) > 1 else np.nan),
        },
        {"Metric": "Skew (returns)", "Value": fmt_num(float(ex.skew()) if len(ex) else np.nan)},
        {"Metric": "Kurtosis (returns)", "Value": fmt_num(float(ex.kurt()) if len(ex) else np.nan)},
        {"Metric": "Expectancy (per day)", "Value": fmt_cash(expectancy)},
        {"Metric": "Max DD Duration (bars)", "Value": f"{max_dur:d}"},
        {"Metric": "Annualization", "Value": f"{ann:d}"},
    ]
    return rows
