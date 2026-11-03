"""Carrega o modelo ONNX e o metadata.json. O app não conhece scikit-learn nem pandas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.config import get_path, load_config
from tools.model_io import load_onnx_session, predict_records, read_metadata


class Predictor:
    def __init__(self, model_path: Path, metadata_path: Path) -> None:
        self.session = load_onnx_session(model_path)
        self.metadata = read_metadata(metadata_path)
        if not self.metadata:
            raise FileNotFoundError(f"{metadata_path} não encontrado. Rode `make train`.")
        self.features: list[str] = self.metadata["features"]
        self.classes: list[str] | None = self.metadata.get("classes")

    @classmethod
    def from_config(cls, config: dict[str, Any] | None = None) -> Predictor:
        config = config or load_config()
        models_dir = get_path("models", config)
        return cls(
            models_dir / config["model"]["file"], models_dir / config["model"]["metadata_file"]
        )

    def validate(self, record: dict[str, Any]) -> list[str]:
        """Lista de erros de schema (features faltando ou desconhecidas)."""
        errors = [f"feature ausente: {f}" for f in self.features if f not in record]
        errors += [f"feature desconhecida: {k}" for k in record if k not in self.features]
        return errors

    def predict(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = predict_records(self.session, records, self.features)
        output = []
        for item in results:
            probabilities = None
            if item["probabilities"] is not None and self.classes:
                probabilities = {
                    c: float(p) for c, p in zip(self.classes, item["probabilities"], strict=True)
                }
            prediction = item["prediction"]
            output.append(
                {
                    "prediction": prediction if isinstance(prediction, str) else float(prediction),
                    "probabilities": probabilities,
                }
            )
        return output
