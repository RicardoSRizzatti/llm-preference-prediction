"""Transform: limpa, padroniza e aplica regras de negócio. Lê data/raw, grava data/interim.

O que NÃO entra aqui: pré-processamento que o modelo precisa na hora da previsão
(escala, encoding, features derivadas). Isso vai no Pipeline do ml/train.py, para
ser exportado junto no ONNX e o app não ter que reimplementar.

Uso: make transform  (ou: uv run python -m etl.transform)
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from tools.config import load_config
from tools.data_io import read_local, write_local
from tools.frames import require_columns, snake_case_columns
from tools.log import get_logger

logger = get_logger(__name__)

# Regra de negócio do exemplo: o código numérico da fonte vira o nome da espécie.
TARGET_NAMES = {0: "setosa", 1: "versicolor", 2: "virginica"}


def transform(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    features: list[str] = config["data"]["features"]
    target: str = config["data"]["target"]

    df = snake_case_columns(df)  # 'sepal length (cm)' → 'sepal_length'
    df = df.rename(columns={"target": target})
    df[target] = df[target].map(TARGET_NAMES)

    require_columns(df, [*features, target])
    df = df[[*features, target]]

    n_before = len(df)
    df = df.dropna().drop_duplicates().reset_index(drop=True)
    if dropped := n_before - len(df):
        logger.info("Transform: %d linhas removidas (nulos/duplicadas)", dropped)

    df[features] = df[features].astype("float64")
    return df


def main() -> None:
    config = load_config()
    table = config["data"]["table"]
    df = transform(read_local(table, "raw", config), config)
    path = write_local(df, table, "interim", config)
    logger.info("Transform: %d linhas → %s", len(df), path)


if __name__ == "__main__":
    main()
