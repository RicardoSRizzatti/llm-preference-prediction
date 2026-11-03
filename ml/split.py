"""Split: separa treino e teste a partir dos dados processados (lidos do destino do load).

Saída: data/split/train.parquet e data/split/test.parquet.
O conjunto de teste só é usado pelo evaluate — nunca no treino.

Uso: make split  (ou: uv run python -m ml.split)
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from tools.config import load_config
from tools.data_io import read_processed, write_local
from tools.log import get_logger

logger = get_logger(__name__)


def split(df: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    params = config["split"]
    target = config["data"]["target"]
    train, test = train_test_split(
        df,
        test_size=params["test_size"],
        random_state=config["project"]["seed"],
        stratify=df[target] if params.get("stratify") else None,
    )
    return train.reset_index(drop=True), test.reset_index(drop=True)


def main() -> None:
    config = load_config()
    train, test = split(read_processed(config), config)
    write_local(train, "train", "split", config)
    write_local(test, "test", "split", config)
    logger.info("Split: treino=%d, teste=%d", len(train), len(test))


if __name__ == "__main__":
    main()
