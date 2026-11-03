"""API FastAPI: expõe o modelo ONNX e serve o front React (build em app/frontend/dist).

Rotas:
  GET  /api/health         status e se o modelo foi carregado
  GET  /api/model          metadata do modelo (features, classes, métricas)
  POST /api/predict        uma previsão
  POST /api/predict/batch  várias previsões (usado na análise de sensibilidade do front)
  GET  /docs               documentação interativa (Swagger)

Uso local: make app   |   Docker: make docker
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.predictor import Predictor
from app.api.schemas import (
    HealthResponse,
    ModelInfo,
    PredictBatchRequest,
    PredictBatchResponse,
    Prediction,
    PredictRequest,
)
from tools.log import get_logger

logger = get_logger(__name__)
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        app.state.predictor = Predictor.from_config()
        logger.info("Modelo carregado: %d features", len(app.state.predictor.features))
    except FileNotFoundError as exc:
        logger.warning("API sem modelo: %s", exc)
        app.state.predictor = None
    yield


app = FastAPI(title="Data Science Template", version="0.1.0", lifespan=lifespan)
api = APIRouter(prefix="/api", tags=["modelo"])


def _predictor(request: Request) -> Predictor:
    predictor = request.app.state.predictor
    if predictor is None:
        raise HTTPException(503, "Modelo não carregado. Rode `make train` e reinicie a API.")
    return predictor


def _validate(predictor: Predictor, records: list[dict]) -> None:
    errors = [f"[{i}] {e}" for i, r in enumerate(records) for e in predictor.validate(r)]
    if errors:
        raise HTTPException(422, errors[:20])


@api.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=request.app.state.predictor is not None)


@api.get("/model", response_model=ModelInfo)
def model_info(request: Request) -> ModelInfo:
    return ModelInfo(**_predictor(request).metadata)


@api.post("/predict", response_model=Prediction)
def predict(body: PredictRequest, request: Request) -> Prediction:
    predictor = _predictor(request)
    _validate(predictor, [body.features])
    return Prediction(**predictor.predict([body.features])[0])


@api.post("/predict/batch", response_model=PredictBatchResponse)
def predict_batch(body: PredictBatchRequest, request: Request) -> PredictBatchResponse:
    predictor = _predictor(request)
    _validate(predictor, body.instances)
    return PredictBatchResponse(
        predictions=[Prediction(**p) for p in predictor.predict(body.instances)]
    )


app.include_router(api)


# ------------------------------------------------------------------ front (SPA)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(404, "Rota não encontrada")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    logger.info("Front não encontrado em %s — rode `make front-build`.", FRONTEND_DIST)
