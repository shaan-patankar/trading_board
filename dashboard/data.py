from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd


def read_strategy_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    date_col = None
    for c in ["date", "Date", "datetime", "Timestamp", "Unnamed: 0"]:
        if c in df.columns:
            date_col = c
            break
    if date_col is None:
        raise ValueError(f"Could not find a date column in {path}. Columns={list(df.columns)}")

    df = df.rename(columns={date_col: "date"}).copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    product_cols = [c for c in df.columns if c != "date"]
    for c in product_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df[product_cols] = df[product_cols].fillna(0.0)
    return df


def apply_position_sizes(
    df: pd.DataFrame,
    strategy: str,
    position_sizes: Dict[str, Dict[str, float]],
    default_size: float = 1.0,
) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    sizes = position_sizes.get(strategy, {})
    product_cols = [c for c in df.columns if c != "date"]
    if not sizes and default_size == 1.0:
        return df

    scaled = df.copy()
    for col in product_cols:
        size = float(sizes.get(col, default_size))
        scaled[col] = scaled[col] * size
    return scaled


def load_strategies(
    strategy_files: Dict[str, Path],
    logger: logging.Logger,
    position_sizes: Dict[str, Dict[str, float]],
    default_size: float = 1.0,
) -> Dict[str, pd.DataFrame]:
    strategies: Dict[str, pd.DataFrame] = {}
    for name, path in strategy_files.items():
        try:
            df = read_strategy_csv(path)
            strategies[name] = apply_position_sizes(df, name, position_sizes, default_size)
        except FileNotFoundError:
            logger.warning("Missing CSV for %s: %s", name, path)
        except ValueError as exc:
            logger.warning("Skipping %s due to invalid data: %s", name, exc)
    return strategies


def products_for_strategy(strategies: Dict[str, pd.DataFrame], strategy: str) -> List[str]:
    df = strategies.get(strategy)
    if df is None:
        return []
    return [c for c in df.columns if c != "date"]


def portfolio_dataframe(strategies: Dict[str, pd.DataFrame], selected_strategies: List[str]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for strategy in selected_strategies:
        df = strategies.get(strategy)
        if df is None:
            continue
        products = products_for_strategy(strategies, strategy)
        frame = df[["date"]].copy()
        frame[strategy] = df[products].sum(axis=1)
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["date"])

    merged = frames[0]
    for frame in frames[1:]:
        merged = pd.merge(merged, frame, on="date", how="outer")

    merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
    merged = merged.sort_values("date").reset_index(drop=True)
    merged = merged.fillna(0.0)
    return merged
