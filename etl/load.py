"""Load: publica os dados tratados no destino configurado em `load.destination`.

- local (padrão): data/processed/<tabela>.parquet
- bigquery: <projeto>.<dataset>.<tabela>
- gcs: gs://<bucket>/<prefixo>/processed/<tabela>.parquet

Uso: make load  (ou: uv run python -m etl.load)
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from tools.config import load_config
from tools.data_io import read_local, write_processed
from tools.log import get_logger

logger = get_logger(__name__)


def load(df: pd.DataFrame, config: dict[str, Any]) -> str:
    return write_processed(df, config)


def main() -> None:
    config = load_config()
    df = read_local(config["data"]["table"], "interim", config)
    location = load(df, config)
    logger.info("Load: %d linhas → %s", len(df), location)


if __name__ == "__main__":
    main()
