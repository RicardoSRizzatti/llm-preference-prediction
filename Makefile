SHELL := /bin/bash
.DEFAULT_GOAL := help

# Variáveis do .env (GCP_PROJECT, GCS_BUCKET, CONFIG_PATH...) ficam disponíveis para os comandos.
ifneq (,$(wildcard .env))
include .env
export
endif

UV    ?= uv
RUN   := $(UV) run
FRONT := app/frontend
IMAGE ?= datascience-template
PORT  ?= 8000

.PHONY: help setup setup-gcp front-install \
        extract transform load etl split fit evaluate train all \
        app front-dev front-build dev docker-build docker-run docker \
        test lint format check notebook clean clean-data

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------- ambiente
setup: ## Instala dependências Python (uv) e do front (npm)
	$(UV) sync
	$(MAKE) front-install

setup-gcp: ## Instala também o grupo gcp (BigQuery / Cloud Storage)
	$(UV) sync --group gcp

front-install: ## Instala as dependências do front
	cd $(FRONT) && npm ci

# ---------------------------------------------------------------------- ETL
extract: ## ETL: fonte → data/raw
	$(RUN) python -m etl.extract

transform: ## ETL: data/raw → data/interim
	$(RUN) python -m etl.transform

load: ## ETL: data/interim → destino (local | bigquery | gcs)
	$(RUN) python -m etl.load

etl: ## ETL completo (extract → transform → load)
	$(MAKE) extract
	$(MAKE) transform
	$(MAKE) load

# ----------------------------------------------------------------------- ML
split: ## ML: dados processados → data/split (treino/teste)
	$(RUN) python -m ml.split

fit: ## ML: treina e salva models/model.onnx + metadata.json
	$(RUN) python -m ml.train

evaluate: ## ML: métricas do ONNX no teste → metadata.json
	$(RUN) python -m ml.evaluate

train: ## ML completo (split → fit → evaluate)
	$(MAKE) split
	$(MAKE) fit
	$(MAKE) evaluate

all: ## Pipeline completo (etl + train)
	$(MAKE) etl
	$(MAKE) train

# ---------------------------------------------------------------------- app
app: ## API + front buildado em http://localhost:8000
	$(RUN) uvicorn app.api.main:app --reload --port $(PORT)

front-dev: ## Front com hot reload em http://localhost:5173 (precisa da API rodando)
	cd $(FRONT) && npm run dev

front-build: ## Gera o build do front em app/frontend/dist
	cd $(FRONT) && npm run build

dev: ## API (8000) + front com hot reload (5173) juntos — Ctrl+C encerra os dois
	@trap 'kill 0' EXIT; \
	$(RUN) uvicorn app.api.main:app --reload --port $(PORT) & \
	cd $(FRONT) && npm run dev

docker-build: ## Build da imagem (front + API + modelo)
	docker build -t $(IMAGE) .

docker-run: ## Sobe o container em http://localhost:$(PORT)
	docker run --rm -p $(PORT):8000 --name $(IMAGE) $(IMAGE)

docker: docker-build docker-run ## Build + run do container

# ------------------------------------------------------------------ qualidade
test: ## Testes (pytest)
	$(RUN) pytest

lint: ## Lint Python (ruff) + checagem de tipos do front
	$(RUN) ruff check .
	$(RUN) ruff format --check .
	cd $(FRONT) && npm run typecheck

format: ## Formata o código Python
	$(RUN) ruff format .
	$(RUN) ruff check --fix .

check: lint test ## Tudo que a CI roda

notebook: ## Abre o Jupyter Lab (sem instalar no projeto)
	$(RUN) --with jupyterlab jupyter lab

# ------------------------------------------------------------------ limpeza
clean: ## Remove caches e build do front
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache $(FRONT)/dist

clean-data: ## Apaga os dados gerados em data/ (mantém a estrutura)
	find data -type f ! -name .gitkeep -delete
