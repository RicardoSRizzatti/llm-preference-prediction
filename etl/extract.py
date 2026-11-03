"""Extract: busca o dado na fonte e grava como veio em data/raw.

Responsabilidade única: trazer o dado. Limpeza e regras de negócio ficam no transform.

Exemplo: dataset Iris do scikit-learn. Troque `extract()` pela sua fonte
(SQL, API, BigQuery, arquivos, sensores...).

Uso: make extract  (ou: uv run python -m etl.extract)
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from tools.config import load_config
from tools.data_io import write_local
from tools.log import get_logger

logger = get_logger(__name__)


def extract(config: dict[str, Any]) -> pd.DataFrame:
    from sklearn.datasets import load_iris

    return load_iris(as_frame=True).frame


def main() -> None:
    config = load_config()
    df = extract(config)
    path = write_local(df, config["data"]["table"], "raw", config)
    logger.info("Extract: %d linhas × %d colunas → %s", *df.shape, path)


if __name__ == "__main__":
    main()
