"""Contratos de entrada e saída da API (validados pelo Pydantic)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

FeatureValue = float | str

EXAMPLE = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}


class PredictRequest(BaseModel):
    features: dict[str, FeatureValue] = Field(examples=[EXAMPLE])


class PredictBatchRequest(BaseModel):
    instances: list[dict[str, FeatureValue]] = Field(
        min_length=1, max_length=5000, examples=[[EXAMPLE]]
    )


class Prediction(BaseModel):
    prediction: FeatureValue
    probabilities: dict[str, float] | None = None


class PredictBatchResponse(BaseModel):
    predictions: list[Prediction]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ModelInfo(BaseModel):
    project: str | None = None
    title: str | None = None
    task: str
    estimator: str | None = None
    trained_at: str | None = None
    evaluated_at: str | None = None
    git: dict[str, Any] | None = None
    features: list[str]
    feature_stats: dict[str, dict[str, Any]] = {}
    target: str
    classes: list[str] | None = None
    display_names: dict[str, str] = {}
    n_train: int | None = None
    n_test: int | None = None
    metrics: dict[str, Any] | None = None
