"""Operações genéricas com DataFrames, reutilizadas pelo ETL e pelo ML."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

import pandas as pd


def snake_case(name: str, drop_units: bool = True) -> str:
    """'Sepal Length (cm)' → 'sepal_length' (ou 'sepal_length_cm' com drop_units=False)."""
    if drop_units:
        name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name.strip())
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.strip("_").lower()


def snake_case_columns(df: pd.DataFrame, drop_units: bool = True) -> pd.DataFrame:
    renamed = {c: snake_case(str(c), drop_units) for c in df.columns}
    if len(set(renamed.values())) != len(renamed):
        raise ValueError(f"Colunas colidem após snake_case: {renamed}")
    return df.rename(columns=renamed)


def require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes: {missing}. Disponíveis: {list(df.columns)}")


def feature_stats(df: pd.DataFrame, features: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Estatísticas por feature (gravadas no metadata.json e usadas pelo front)."""
    stats: dict[str, dict[str, Any]] = {}
    for col in features:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            stats[col] = {
                "type": "numeric",
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "std": float(series.std()),
            }
        else:
            stats[col] = {
                "type": "categorical",
                "categories": sorted(map(str, series.dropna().unique())),
            }
    return stats
