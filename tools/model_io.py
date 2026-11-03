"""Salvar, carregar e usar modelos. ONNX é o ÚNICO formato aceito neste projeto.

Por que isso é garantido:
- `save_onnx_model` é a única forma de salvar um modelo e só grava `.onnx`;
- ao salvar, o modelo convertido é validado (onnx.checker) e comparado com o
  modelo original (paridade numérica) — se divergir, nada é gravado;
- o app só carrega `.onnx` via onnxruntime (sem pickle/joblib);
- `check_models_dir` (usado nos testes e na CI) falha se aparecer outro formato em models/.

Imports pesados (skl2onnx, onnx, scikit-learn) ficam dentro das funções de
treino, para que o app rode só com o grupo `app` (numpy + onnxruntime).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

MODEL_SUFFIX = ".onnx"
# Arquivos permitidos na pasta models/ (além dos .onnx).
ALLOWED_EXTRA_FILES = {"metadata.json", ".gitkeep", "README.md"}


class OnnxParityError(RuntimeError):
    """O modelo ONNX não reproduz as previsões do modelo original."""


# ------------------------------------------------------------------ validações
def ensure_onnx_path(path: str | Path) -> Path:
    path = Path(path)
    if path.suffix.lower() != MODEL_SUFFIX:
        raise ValueError(
            f"Modelos devem ser salvos em ONNX ({MODEL_SUFFIX}). Recebido: '{path.name}'."
        )
    return path


def check_models_dir(models_dir: str | Path) -> list[Path]:
    """Retorna os arquivos proibidos encontrados em models/ (lista vazia = ok)."""
    models_dir = Path(models_dir)
    if not models_dir.exists():
        return []
    return [
        p
        for p in sorted(models_dir.rglob("*"))
        if p.is_file() and p.suffix.lower() != MODEL_SUFFIX and p.name not in ALLOWED_EXTRA_FILES
    ]


# -------------------------------------------------------------------- conversão
def _final_estimator(model: Any) -> Any:
    return model.steps[-1][1] if hasattr(model, "steps") else model


def convert_to_onnx(model: Any, X_sample: Any, target_opset: int | None = None):
    """Converte um modelo/Pipeline do scikit-learn para ONNX.

    - Features todas numéricas → um único input float32 chamado "input".
    - Features mistas (ex.: strings categóricas) → um input por coluna, com o nome
      da coluna (use ColumnTransformer com nomes de coluna no Pipeline).
    Classificadores saem com `label` e `probabilities` (zipmap desativado).
    """
    import pandas as pd
    from skl2onnx import to_onnx
    from skl2onnx.common.data_types import FloatTensorType
    from sklearn.base import is_classifier

    options = {id(_final_estimator(model)): {"zipmap": False}} if is_classifier(model) else None
    kwargs: dict[str, Any] = {"options": options}
    if target_opset is not None:
        kwargs["target_opset"] = target_opset

    if isinstance(X_sample, pd.DataFrame) and not all(
        pd.api.types.is_numeric_dtype(t) for t in X_sample.dtypes
    ):
        return to_onnx(model, X_sample.iloc[:1], **kwargs)

    n_features = np.asarray(X_sample).shape[1]
    return to_onnx(model, initial_types=[("input", FloatTensorType([None, n_features]))], **kwargs)


def _reference_outputs(model: Any, X: Any) -> np.ndarray:
    """Saída do modelo original usada na comparação de paridade."""
    from sklearn.base import is_classifier

    if is_classifier(model) and hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(X), dtype=np.float64)
    return np.asarray(model.predict(X), dtype=np.float64).reshape(len(X), -1)


def save_onnx_model(
    model: Any,
    X_sample: Any,
    path: str | Path,
    tolerance: float = 1e-4,
    target_opset: int | None = None,
) -> dict[str, Any]:
    """Converte, valida e grava o modelo em ONNX. Única forma de salvar modelos.

    `X_sample` deve ser uma amostra representativa (ex.: o conjunto de treino),
    usada para conferir que o ONNX reproduz o modelo original.
    """
    import onnx

    path = ensure_onnx_path(path)
    onx = convert_to_onnx(model, X_sample, target_opset=target_opset)
    onnx.checker.check_model(onx)

    session = _new_session(onx.SerializeToString())
    result = predict_onnx(session, X_sample)
    onnx_out = (
        result["probabilities"] if result["probabilities"] is not None else result["prediction"]
    )
    onnx_out = np.asarray(onnx_out, dtype=np.float64).reshape(len(X_sample), -1)
    max_diff = float(np.max(np.abs(onnx_out - _reference_outputs(model, X_sample))))
    if max_diff > tolerance:
        raise OnnxParityError(
            f"ONNX diverge do modelo original: diferença máxima {max_diff:.2e} > {tolerance:.0e}."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(onx.SerializeToString())
    return {
        "format": "onnx",
        "opset": {d.domain or "ai.onnx": d.version for d in onx.opset_import},
        "inputs": [i.name for i in session.get_inputs()],
        "outputs": [o.name for o in session.get_outputs()],
        "parity_max_abs_diff": max_diff,
    }


# --------------------------------------------------------------------- inferência
def _new_session(model: str | bytes):
    import onnxruntime as ort

    # Log do onnxruntime só com erros durante a inferência.
    # (O aviso "GetPciBusId" que aparece em VMs/WSL ao iniciar é inofensivo.)
    ort.set_default_logger_severity(3)
    return ort.InferenceSession(model, providers=["CPUExecutionProvider"])


def load_onnx_session(path: str | Path):
    path = ensure_onnx_path(path)
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado em {path}. Rode `make train`.")
    return _new_session(str(path))


_ORT_DTYPES = {
    "tensor(float)": np.float32,
    "tensor(double)": np.float64,
    "tensor(int64)": np.int64,
    "tensor(int32)": np.int32,
    "tensor(string)": np.object_,
    "tensor(bool)": np.bool_,
}


def _build_feed(session, X: Any, feature_names: list[str] | None = None) -> dict[str, np.ndarray]:
    inputs = session.get_inputs()
    if len(inputs) == 1:
        if hasattr(X, "columns") and feature_names:
            X = X[feature_names]
        dtype = _ORT_DTYPES.get(inputs[0].type, np.float32)
        return {inputs[0].name: np.asarray(X, dtype=dtype)}

    # Um input por coluna (modelos convertidos a partir de DataFrame com tipos mistos).
    feed = {}
    for inp in inputs:
        dtype = _ORT_DTYPES.get(inp.type, np.float32)
        feed[inp.name] = np.asarray(X[inp.name], dtype=dtype).reshape(-1, 1)
    return feed


def predict_onnx(session, X: Any, feature_names: list[str] | None = None) -> dict[str, Any]:
    """Roda o modelo ONNX.

    Retorna {"prediction": array, "probabilities": array | None}.
    `X` pode ser DataFrame, array 2D ou (para modelos com um input por coluna) dict de colunas.
    """
    feed = _build_feed(session, X, feature_names)
    names = [o.name for o in session.get_outputs()]
    outputs = dict(zip(names, session.run(None, feed), strict=True))

    if "label" in outputs:  # classificador
        return {"prediction": outputs["label"], "probabilities": outputs.get("probabilities")}
    prediction = outputs.get("variable", next(iter(outputs.values())))
    return {"prediction": np.asarray(prediction).reshape(-1), "probabilities": None}


def predict_records(
    session, records: list[dict[str, Any]], features: list[str]
) -> list[dict[str, Any]]:
    """Previsão a partir de registros (dicts), sem pandas — usada pelo app.

    Retorna, por registro, {"prediction": valor, "probabilities": array | None}.
    """
    if len(session.get_inputs()) == 1:
        X: Any = [[record[f] for f in features] for record in records]
    else:
        X = {f: [record[f] for record in records] for f in features}

    result = predict_onnx(session, X)
    probabilities = result["probabilities"]
    return [
        {
            "prediction": result["prediction"][i].item()
            if hasattr(result["prediction"][i], "item")
            else result["prediction"][i],
            "probabilities": None if probabilities is None else probabilities[i],
        }
        for i in range(len(records))
    ]


# ---------------------------------------------------------------------- metadata
def read_metadata(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_metadata(path: str | Path, metadata: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
