from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from tools.config import get_path, load_config

MODEL_EXISTS = (get_path("models") / load_config()["model"]["file"]).exists()
needs_model = pytest.mark.skipif(not MODEL_EXISTS, reason="rode `make train` para gerar o modelo")

SAMPLE = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # o `with` executa o lifespan (carrega o modelo)
        yield c


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": MODEL_EXISTS}


@needs_model
def test_model_info(client: TestClient) -> None:
    info = client.get("/api/model").json()
    assert info["features"] == list(SAMPLE)
    assert info["task"] == "classification"
    assert set(info["feature_stats"]) == set(SAMPLE)


@needs_model
def test_predict(client: TestClient) -> None:
    body = client.post("/api/predict", json={"features": SAMPLE}).json()
    assert body["prediction"] == "setosa"
    assert abs(sum(body["probabilities"].values()) - 1) < 1e-5


@needs_model
def test_predict_batch(client: TestClient) -> None:
    instances = [SAMPLE, {**SAMPLE, "petal_length": 5.5, "petal_width": 2.1}]
    body = client.post("/api/predict/batch", json={"instances": instances}).json()
    assert [p["prediction"] for p in body["predictions"]] == ["setosa", "virginica"]


@needs_model
def test_predict_validates_schema(client: TestClient) -> None:
    missing = {k: v for k, v in SAMPLE.items() if k != "petal_width"}
    response = client.post("/api/predict", json={"features": {**missing, "cor": 1}})
    assert response.status_code == 422
    detail = " ".join(response.json()["detail"])
    assert "petal_width" in detail and "cor" in detail


def test_unknown_api_route_is_404(client: TestClient) -> None:
    assert client.get("/api/nao-existe").status_code == 404
