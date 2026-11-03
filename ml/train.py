"""Train: treina o Pipeline e salva o modelo em ONNX (models/model.onnx + metadata.json).

Todo pré-processamento que o modelo precisa na previsão (escala, encoding,
features derivadas) fica DENTRO do Pipeline, para ser exportado no ONNX.

Ciclo de trabalho: ajuste build_pipeline/params → make train → veja as métricas
do evaluate → repita. Quando estiver bom, comite models/.

Uso: make train  (roda split → train → evaluate)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sklearn.base import is_classifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from tools.config import get_path, load_config
from tools.data_io import read_local
from tools.frames import feature_stats
from tools.git_info import current_commit
from tools.log import get_logger
from tools.model_io import save_onnx_model, write_metadata

logger = get_logger(__name__)


def build_pipeline(params: dict[str, Any], seed: int) -> Pipeline:
    """Defina aqui o modelo. Só use componentes com conversor ONNX (skl2onnx/onnxmltools)."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(**params, random_state=seed)),
        ]
    )


def main() -> None:
    config = load_config()
    features: list[str] = config["data"]["features"]
    target: str = config["data"]["target"]
    model_cfg = config["model"]

    train_df = read_local("train", "split", config)
    X, y = train_df[features], train_df[target]

    pipeline = build_pipeline(model_cfg.get("params") or {}, config["project"]["seed"])
    pipeline.fit(X, y)

    models_dir = get_path("models", config, create=True)
    onnx_info = save_onnx_model(
        pipeline,
        X,
        models_dir / model_cfg["file"],
        tolerance=model_cfg.get("parity_tolerance", 1e-4),
        target_opset=model_cfg.get("target_opset"),
    )

    classifier = is_classifier(pipeline)
    metadata = {
        "project": config["project"]["name"],
        "title": config["project"].get("title"),
        "model_file": model_cfg["file"],
        "task": "classification" if classifier else "regression",
        "estimator": type(pipeline[-1]).__name__,
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git": current_commit(),
        "features": features,
        "feature_stats": feature_stats(train_df, features),
        "target": target,
        "classes": [str(c) for c in pipeline.classes_] if classifier else None,
        "display_names": config["data"].get("display_names") or {},
        "params": model_cfg.get("params") or {},
        "n_train": len(train_df),
        "onnx": onnx_info,
        "metrics": None,  # preenchido pelo ml/evaluate.py
    }
    write_metadata(models_dir / model_cfg["metadata_file"], metadata)
    logger.info(
        "Train: %s salvo em %s (paridade ONNX: %.1e)",
        metadata["estimator"],
        models_dir / model_cfg["file"],
        onnx_info["parity_max_abs_diff"],
    )


if __name__ == "__main__":
    main()
