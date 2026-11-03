"""Evaluate: mede o modelo ONNX (o mesmo que vai para o app) no conjunto de teste.

As métricas são gravadas em models/metadata.json e exibidas no front.

Uso: make evaluate  (ou: uv run python -m ml.evaluate)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn import metrics as skm

from tools.config import get_path, load_config
from tools.data_io import read_local
from tools.log import get_logger
from tools.model_io import load_onnx_session, predict_onnx, read_metadata, write_metadata

logger = get_logger(__name__)


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, classes: list[str]) -> dict:
    report = skm.classification_report(
        y_true, y_pred, labels=classes, output_dict=True, zero_division=0
    )
    return {
        "accuracy": float(skm.accuracy_score(y_true, y_pred)),
        "f1_macro": float(skm.f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision_macro": float(
            skm.precision_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "recall_macro": float(skm.recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_matrix": {
            "labels": classes,
            "matrix": skm.confusion_matrix(y_true, y_pred, labels=classes).tolist(),
        },
        "per_class": {
            c: {k: float(report[c][k]) for k in ("precision", "recall", "f1-score", "support")}
            for c in classes
        },
    }


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "mae": float(skm.mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(skm.mean_squared_error(y_true, y_pred))),
        "r2": float(skm.r2_score(y_true, y_pred)),
    }


def evaluate(session, test_df: pd.DataFrame, metadata: dict[str, Any]) -> dict[str, Any]:
    result = predict_onnx(session, test_df, feature_names=metadata["features"])
    y_true = test_df[metadata["target"]].to_numpy()
    y_pred = np.asarray(result["prediction"])

    if metadata["task"] == "classification":
        return classification_metrics(y_true.astype(str), y_pred.astype(str), metadata["classes"])
    return regression_metrics(y_true.astype(float), y_pred.astype(float))


def main() -> None:
    config = load_config()
    models_dir = get_path("models", config)
    metadata_path = models_dir / config["model"]["metadata_file"]

    metadata = read_metadata(metadata_path)
    if not metadata:
        raise FileNotFoundError(f"{metadata_path} não encontrado. Rode o treino antes.")

    session = load_onnx_session(models_dir / config["model"]["file"])
    test_df = read_local("test", "split", config)
    metrics = evaluate(session, test_df, metadata)

    metadata["metrics"] = metrics
    metadata["n_test"] = len(test_df)
    metadata["evaluated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    write_metadata(metadata_path, metadata)

    summary = {k: round(v, 4) for k, v in metrics.items() if isinstance(v, float)}
    logger.info("Evaluate (ONNX, n=%d): %s", len(test_df), summary)


if __name__ == "__main__":
    main()
