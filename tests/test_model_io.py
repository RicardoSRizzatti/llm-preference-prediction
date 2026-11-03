"""Regras do formato ONNX: só .onnx é aceito e o modelo convertido reproduz o original."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import load_iris, make_regression
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from tools import model_io
from tools.model_io import (
    OnnxParityError,
    check_models_dir,
    ensure_onnx_path,
    load_onnx_session,
    predict_onnx,
    predict_records,
    save_onnx_model,
)


@pytest.fixture(scope="module")
def iris() -> tuple[pd.DataFrame, pd.Series]:
    data = load_iris(as_frame=True)
    X = data.data.set_axis(["sepal_length", "sepal_width", "petal_length", "petal_width"], axis=1)
    y = data.target.map(dict(enumerate(data.target_names)))
    return X, y


@pytest.fixture(scope="module")
def classifier(iris) -> Pipeline:
    X, y = iris
    return Pipeline(
        [("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=500))]
    ).fit(X, y)


@pytest.mark.parametrize("name", ["model.joblib", "model.pkl", "model.pickle", "model"])
def test_only_onnx_paths_are_accepted(name: str) -> None:
    with pytest.raises(ValueError, match="ONNX"):
        ensure_onnx_path(name)


def test_save_rejects_non_onnx(tmp_path: Path, classifier, iris) -> None:
    with pytest.raises(ValueError, match="ONNX"):
        save_onnx_model(classifier, iris[0], tmp_path / "model.joblib")
    assert not any(tmp_path.iterdir())


def test_classifier_roundtrip(tmp_path: Path, classifier, iris) -> None:
    X, _ = iris
    path = tmp_path / "model.onnx"
    info = save_onnx_model(classifier, X, path)

    assert path.exists()
    assert info["format"] == "onnx"
    assert info["parity_max_abs_diff"] < 1e-4
    assert info["outputs"] == ["label", "probabilities"]

    result = predict_onnx(load_onnx_session(path), X)
    np.testing.assert_array_equal(result["prediction"], classifier.predict(X))
    np.testing.assert_allclose(result["probabilities"], classifier.predict_proba(X), atol=1e-4)


def test_regressor_roundtrip(tmp_path: Path) -> None:
    X, y = make_regression(n_samples=200, n_features=5, noise=0.1, random_state=0)
    model = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())]).fit(X, y)
    path = tmp_path / "reg.onnx"
    save_onnx_model(model, X, path, tolerance=1e-2)

    result = predict_onnx(load_onnx_session(path), X)
    assert result["probabilities"] is None
    np.testing.assert_allclose(result["prediction"], model.predict(X), rtol=1e-4, atol=1e-2)


def test_parity_failure_writes_nothing(tmp_path: Path, classifier, iris, monkeypatch) -> None:
    original = model_io._reference_outputs
    monkeypatch.setattr(model_io, "_reference_outputs", lambda m, X: original(m, X) + 0.5)
    path = tmp_path / "model.onnx"
    with pytest.raises(OnnxParityError):
        save_onnx_model(classifier, iris[0], path)
    assert not path.exists()


def test_predict_records_matches_dataframe(tmp_path: Path, classifier, iris) -> None:
    X, _ = iris
    path = tmp_path / "model.onnx"
    save_onnx_model(classifier, X, path)
    session = load_onnx_session(path)

    records = X.head(5).to_dict(orient="records")
    results = predict_records(session, records, list(X.columns))
    assert [r["prediction"] for r in results] == list(classifier.predict(X.head(5)))
    assert all(abs(float(np.sum(r["probabilities"])) - 1) < 1e-5 for r in results)


def test_check_models_dir_flags_other_formats(tmp_path: Path) -> None:
    (tmp_path / "model.onnx").write_bytes(b"")
    (tmp_path / "metadata.json").write_text("{}")
    (tmp_path / "old.joblib").write_bytes(b"")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "x.pkl").write_bytes(b"")
    assert [p.name for p in check_models_dir(tmp_path)] == ["old.joblib", "x.pkl"]
