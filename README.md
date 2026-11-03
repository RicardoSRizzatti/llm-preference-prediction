# Previsão de preferência humana entre respostas de LLMs

Dado um prompt e as respostas de dois modelos de linguagem, prever **qual resposta uma pessoa vai preferir**, ou se ela vai considerar empate. Os dados vêm de conversas reais do **Chatbot Arena** e o problema é o da competição **LLM Classification Finetuning** do Kaggle.

> 🚧 Projeto em andamento. O roteiro e o status de cada etapa estão na seção [Roteiro](#roteiro).

---

## Contexto

No Chatbot Arena, o usuário escreve um prompt, recebe lado a lado as respostas de dois LLMs anônimos e vota na melhor, ou declara empate. Esses votos são a base de rankings públicos de modelos e são exatamente o tipo de sinal usado para alinhar LLMs com aprendizado por reforço a partir de feedback humano (RLHF): antes de otimizar um modelo para agradar as pessoas, é preciso um **modelo de recompensa** que preveja o que elas preferem.

Prever esse voto não é trivial. As pessoas não julgam só pelo conteúdo: há vieses conhecidos de posição (a resposta exibida primeiro), de tamanho (respostas mais longas tendem a ganhar) e de estilo (formatação, listas, tom). Um bom modelo precisa capturar a qualidade real da resposta e também esses atalhos humanos.

## O desafio

Cada exemplo tem um prompt (às vezes uma conversa de vários turnos), a resposta A e a resposta B. O modelo deve devolver três probabilidades: A vence, B vence ou empate.

O que torna o problema difícil:

- **Rótulo ruidoso e subjetivo**: pessoas diferentes votariam de forma diferente na mesma comparação, e o empate é frequente.
- **Textos longos**: prompt e duas respostas juntos passam facilmente do limite de contexto de modelos menores, o que obriga a truncar com critério.
- **Vieses de posição e de tamanho**, que o modelo precisa aprender sem depender só deles.
- **Simetria**: trocar A e B deveria trocar as probabilidades, e o modelo nem sempre respeita isso sozinho.
- **Restrição de execução**: a submissão roda num notebook do Kaggle **sem internet**, em até 9 horas de CPU ou GPU, o que limita o tamanho do modelo usado na inferência.

## Objetivo e métrica

**Objetivo:** construir um classificador de preferência com log loss bem abaixo do baseline uniforme (ln 3 ≈ 1,0986), partindo de um modelo de features leve e chegando a um modelo de linguagem ajustado (*fine-tuning*), e servir o modelo por uma API que recebe prompt e respostas e devolve as probabilidades.

**Métrica oficial:** log loss multiclasse sobre as três probabilidades:

```
LogLoss = −(1/N) · Σ_i Σ_c  y_ic · ln(p_ic),    c ∈ {winner_model_a, winner_model_b, winner_tie}
```

Quanto menor, melhor. A métrica pune muito previsões confiantes e erradas, então a calibração das probabilidades importa tanto quanto o acerto.

Métricas complementares: acurácia, matriz de confusão (com atenção ao empate) e consistência ao trocar A e B.

## Dados

| | |
|---|---|
| **Competição (dados e regras)** | <https://www.kaggle.com/competitions/llm-classification-finetuning> |
| **Tipo** | *Getting Started* contínua, aberta até 01/07/2030 |
| **Origem** | Votos do Chatbot Arena (LMSYS) |
| **`train.csv`** | `id`, `model_a`, `model_b`, `prompt`, `response_a`, `response_b`, `winner_model_a`, `winner_model_b`, `winner_tie` |
| **`test.csv`** | `id`, `prompt`, `response_a`, `response_b` (sem os nomes dos modelos) |
| **Submissão** | `submission.csv` com `id`, `winner_model_a`, `winner_model_b`, `winner_tie`, gerado por notebook do Kaggle; modelos pré-treinados e dados externos são permitidos |

Os campos de texto guardam listas de mensagens (uma por turno da conversa). Os dados **não são versionados** neste repositório. Para reproduzir, aceite as regras na página da competição e baixe com a CLI do Kaggle (token em `~/.kaggle/kaggle.json`):

```bash
make data   # usa a CLI do Kaggle via uv e descompacta em data/raw/llm-classification-finetuning
```

## Sobre o projeto

| | |
|---|---|
| **Problema** | Prever a preferência humana (A, B ou empate) entre duas respostas de LLMs ao mesmo prompt. |
| **Dados** | Conversas e votos do Chatbot Arena, via competição LLM Classification Finetuning (Kaggle). |
| **Abordagem (planejada)** | 1) Baseline de features (tamanho, diferença de tamanho, formatação, sobreposição com o prompt) com gradient boosting, exportado em ONNX. 2) *Fine-tuning* em PyTorch de um modelo de linguagem como classificador de pares, com LoRA, aumentando os dados com a troca de A e B. 3) Calibração e combinação dos modelos. Validação cruzada estratificada. |
| **Métrica principal** | Log loss multiclasse. |
| **Resultado** | A preencher: ver `models/metadata.json` ou a seção *Qualidade do modelo* no app. |

## Roteiro

- [ ] Baixar os dados para `data/raw/llm-classification-finetuning` e adaptar `etl/extract.py`
- [ ] Análise exploratória em `notebooks/`: distribuição dos rótulos, taxa de empate, tamanho dos textos, viés de posição e de tamanho, modelos mais frequentes
- [ ] `etl/transform.py`: decodificar as conversas, normalizar textos e gerar a versão com A e B trocados
- [ ] Baseline de features com gradient boosting, exportado em ONNX e servido pela API
- [ ] *Fine-tuning* de um modelo de linguagem em PyTorch com LoRA e estratégia de truncamento para textos longos
- [ ] Calibração das probabilidades e combinação dos modelos
- [ ] Notebook de inferência que roda no Kaggle sem internet dentro do limite de tempo, e submissão
- [ ] Análise de erros: onde o modelo erra, viés de tamanho nas previsões e consistência ao trocar A e B

## Referências

- L. Zheng *et al.*, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", *NeurIPS Datasets and Benchmarks*, 2023. <https://arxiv.org/abs/2306.05685>
- Competição no Kaggle: <https://www.kaggle.com/competitions/llm-classification-finetuning>

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
