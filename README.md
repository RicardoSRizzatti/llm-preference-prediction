# Data Science Template

Template para projetos de ciência de dados, da extração dos dados ao modelo servido num webapp: **ETL → treinamento (ONNX) → API FastAPI + front React**, tudo automatizado com `make` e empacotado em Docker.

O repositório já vem com um exemplo funcionando de ponta a ponta (classificação de espécies do dataset Iris). Ele serve de referência e deve ser substituído pelo seu problema.

---

## Sobre o projeto

> Preencha esta seção em cada projeto criado a partir do template. O texto abaixo descreve o exemplo.

| | |
|---|---|
| **Problema** | Classificar a espécie de uma flor (setosa, versicolor ou virginica) a partir de 4 medidas. |
| **Dados** | Dataset Iris (150 amostras), carregado do scikit-learn em `etl/extract.py`. |
| **Abordagem** | `StandardScaler` + `LogisticRegression`, exportados juntos em ONNX. |
| **Métrica principal** | F1 macro no conjunto de teste (20%, estratificado). |
| **Resultado** | Ver `models/metadata.json` ou a seção *Qualidade do modelo* no app. |

---

## Início rápido

Requisitos: Linux ou WSL, [uv](https://docs.astral.sh/uv/), Node.js 22+, Docker e `make`.

```bash
make setup        # dependências Python (uv) e do front (npm)
make all          # ETL + treino + avaliação → models/model.onnx
make front-build  # build do React
make app          # http://localhost:8000  (API + front)
```

Ou, só com Docker (usa o modelo já versionado em `models/`):

```bash
make docker       # build + run em http://localhost:8000
```

Para desenvolver o front com hot reload: `make dev` (API na 8000 + Vite na 5173).

`make help` lista todos os comandos.

---

## Estrutura

```
├── configs/config.yaml   # caminhos, seed, destino do load, parâmetros do modelo
├── data/                 # NÃO versionado (só a estrutura)
│   ├── raw/              #   saída do extract: dado como veio da fonte
│   ├── interim/          #   saída do transform: limpo, ainda não publicado
│   ├── processed/        #   saída do load quando o destino é local
│   └── split/            #   train.parquet / test.parquet
├── tools/                # biblioteca própria (usada por etl, ml e app)
│   ├── config.py         #   leitura do config e caminhos
│   ├── data_io.py        #   leitura/escrita: local, BigQuery, GCS
│   ├── model_io.py       #   salvar/carregar modelos (somente ONNX)
│   ├── frames.py         #   operações genéricas com DataFrames
│   ├── git_info.py       #   commit usado no treino
│   └── log.py            #   logger padrão
├── etl/
│   ├── extract.py        # fonte → data/raw
│   ├── transform.py      # data/raw → data/interim (limpeza e regras de negócio)
│   └── load.py           # data/interim → destino (local | bigquery | gcs)
├── ml/
│   ├── split.py          # dados processados → treino/teste
│   ├── train.py          # Pipeline → models/model.onnx + metadata.json
│   └── evaluate.py       # métricas do ONNX no teste → metadata.json
├── models/               # VERSIONADO: somente .onnx + metadata.json
├── app/
│   ├── api/              # FastAPI (carrega o ONNX com onnxruntime)
│   └── frontend/         # React + TypeScript + Vite + ECharts
├── notebooks/            # análise exploratória (fora do pipeline)
├── tests/                # pytest
├── Dockerfile            # multi-stage: build do front + API + modelo
└── Makefile              # automação de todos os comandos
```

### Fluxo

```
fonte ─extract─▶ data/raw ─transform─▶ data/interim ─load─▶ processed (local | BigQuery | GCS)
                                                                   │
                                     ml/split ◀────────────────────┘
                                        │
                     data/split ─train─▶ models/model.onnx ─evaluate─▶ metadata.json (métricas)
                                                │
                                   app/api (onnxruntime) ─▶ app/frontend (React)
```

---

## Regras do repositório

Estas regras são verificadas automaticamente em `tests/test_project_rules.py` e na CI.

1. **Direção das dependências.** `etl`, `ml` e `app` importam de `tools`; `tools` não importa de nenhum deles. `app` não importa `etl`, `ml`, scikit-learn nem pandas: ele só conhece o modelo ONNX e o `metadata.json`.
2. **Modelos somente em ONNX.** A única forma de salvar um modelo é `tools.model_io.save_onnx_model`, que:
   - recusa qualquer caminho que não termine em `.onnx`;
   - valida o arquivo com `onnx.checker`;
   - compara as previsões do ONNX com as do modelo original (tolerância em `model.parity_tolerance`) e **não grava nada** se divergirem.

   Além disso, o `.gitignore` ignora qualquer outro arquivo em `models/`, e um teste falha se aparecer `.joblib`, `.pkl` etc.
3. **Pré-processamento dentro do Pipeline.** O ETL limpa e aplica regras de negócio; escala, encoding e features derivadas que o modelo precisa na previsão ficam no `Pipeline` do `ml/train.py`, para serem exportados no ONNX. Assim o app não reimplementa nada.
4. **Avaliação no artefato final.** O `evaluate.py` mede o próprio `model.onnx`, então a métrica exibida é a do modelo que vai para produção.
5. **Dados fora do git, modelos dentro.** `data/` nunca é versionado. `models/` é: o GitHub avisa acima de 50 MB e bloqueia acima de 100 MB; se um modelo crescer, use Git LFS (instruções no `.gitattributes`).

### ONNX: cuidados

- O ONNX trabalha em float32 por padrão: pequenas diferenças numéricas em relação ao scikit-learn são normais (por isso a tolerância).
- Nem todo componente tem conversor. Os nativos do scikit-learn têm; XGBoost e LightGBM convertem via `onnxmltools`; um transformador customizado exige registrar um conversor no `skl2onnx`.
- Features categóricas (texto): use `ColumnTransformer` com nomes de coluna; `convert_to_onnx` cria um input por coluna automaticamente.

---

## Configuração

Tudo fica em `configs/config.yaml`. Para usar outro arquivo: `CONFIG_PATH=configs/outro.yaml make all`.

### Destino dos dados processados

```yaml
load:
  destination: local   # local (padrão) | bigquery | gcs
```

Para BigQuery ou Cloud Storage:

```bash
make setup-gcp                             # instala o grupo gcp
gcloud auth application-default login      # autenticação
cp .env.example .env                       # e preencha GCP_PROJECT / GCS_BUCKET
```

O `ml/split.py` lê os dados processados pela mesma função (`read_processed`), então sempre encontra os dados onde o load gravou.

### Dependências (grupos do uv)

| Grupo | Para quê | Instalado por |
|---|---|---|
| (projeto) | numpy, pyyaml — comuns a todas as etapas | sempre |
| `etl` | pandas, pyarrow | `make setup` |
| `ml` | scikit-learn, skl2onnx, onnx, onnxruntime | `make setup` |
| `app` | fastapi, uvicorn, onnxruntime | `make setup` e Docker |
| `dev` | pytest, ruff, httpx, ipykernel | `make setup` |
| `gcp` | google-cloud-bigquery, google-cloud-storage | `make setup-gcp` |

A imagem Docker instala só o projeto + grupo `app`.

---

## Webapp

### API

| Rota | Descrição |
|---|---|
| `GET /api/health` | status e se o modelo foi carregado |
| `GET /api/model` | metadata: features, estatísticas, classes, métricas |
| `POST /api/predict` | `{"features": {...}}` → previsão e probabilidades |
| `POST /api/predict/batch` | `{"instances": [{...}, ...]}` → várias previsões |
| `GET /docs` | documentação interativa (Swagger) |

### Front

O front é gerado a partir do `metadata.json`: o formulário, a análise de sensibilidade e as métricas se adaptam a qualquer modelo de classificação ou regressão sem mudar código.

Gráficos padronizados ficam em `app/frontend/src/charts/`:

- `theme.ts` — **única fonte de cores**, com paleta categórica validada para daltonismo, escala sequencial e modo escuro;
- `Chart.tsx` — componente base (ciclo de vida do ECharts, redimensionamento e visão em tabela);
- `BarChart`, `LineChart` (com amostragem LTTB e zoom para séries longas) e `HeatmapChart`.

Para um novo tipo de gráfico: registre-o em `charts/echarts.ts` e crie o componente em `charts/` usando `baseOption`, `valueAxis` e `categoryAxis` do tema.

---

## Novo projeto a partir do template

1. No GitHub: **Use this template → Create a new repository**.
2. Preencha a seção *Sobre o projeto* deste README.
3. Ajuste `configs/config.yaml`: nome do projeto, tabela, target e features.
4. Substitua `extract()` pela sua fonte e as regras de `transform()`.
5. Defina o modelo em `build_pipeline()` (`ml/train.py`).
6. `make all`, confira as métricas, itere e comite `models/`.
7. Apague os testes específicos do Iris em `tests/test_api.py` e `tests/test_etl.py` (ou adapte-os).

---

## Qualidade e CI

```bash
make test     # pytest
make lint     # ruff + checagem de tipos do front
make format   # formata o Python
make check    # o mesmo que a CI
```

A CI (`.github/workflows/ci.yml`) roda lint, o pipeline completo, os testes, o build do front e um smoke test da imagem Docker em cada push na `main` e em pull requests.

---

## Dúvidas comuns

- **Aviso `GetPciBusId` do onnxruntime ao iniciar** (comum em WSL e VMs): é inofensivo; o onnxruntime só não reconhece o barramento PCI virtual.
- **`make` reclama de `uv` ou `npm` não encontrados**: instale o uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`) e o Node 22+ (recomendado via `nvm`).
- **Front mostra "Modelo indisponível"**: rode `make all` para gerar `models/model.onnx` e reinicie a API.
- **Mudei o modelo e o app não mudou**: a API carrega o modelo ao iniciar; reinicie (`make app`) ou refaça a imagem (`make docker`).
