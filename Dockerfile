# syntax=docker/dockerfile:1

# ---- 1) Build do front: o Node só existe nesta etapa e não vai para a imagem final ----
FROM node:22-slim AS frontend
WORKDIR /front
COPY app/frontend/package.json app/frontend/package-lock.json ./
RUN npm ci
COPY app/frontend/ ./
RUN npm run build

# ---- 2) Imagem final: Python + dependências de inferência (grupo `app`) + modelo ONNX ----
FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PROJECT_ROOT=/app \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependências primeiro (camada reaproveitada enquanto o uv.lock não muda).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-default-groups --group app --no-install-project

# Só o que a inferência precisa: sem etl/, ml/, data/, notebooks/ ou testes.
COPY tools/ tools/
COPY app/__init__.py app/__init__.py
COPY app/api/ app/api/
COPY configs/ configs/
COPY models/ models/
COPY --from=frontend /front/dist app/frontend/dist

RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
