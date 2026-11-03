# CLAUDE.md

Contexto para o Claude Code neste repositório. O README tem a descrição completa do desafio; aqui ficam o estado atual, as decisões e o que não pode ser quebrado.

## O projeto

Prever a preferência humana entre duas respostas de LLMs ao mesmo prompt (A vence, B vence ou empate), com os dados do Chatbot Arena da competição **LLM Classification Finetuning** do Kaggle.

- **Competição:** <https://www.kaggle.com/competitions/llm-classification-finetuning> (*Getting Started*, aberta até 01/07/2030).
- **Dados:** `make data` usa a CLI do Kaggle (via `uv tool run`) e descompacta em `data/raw/llm-classification-finetuning`. Exige aceitar as regras no site e o token em `~/.kaggle/kaggle.json`. `data/` nunca vai para o git.
- **`train.csv`:** `id`, `model_a`, `model_b`, `prompt`, `response_a`, `response_b`, `winner_model_a`, `winner_model_b`, `winner_tie`. `prompt` e `response_*` são listas (uma mensagem por turno) serializadas como texto: decodificar no transform.
- **`test.csv`:** `id`, `prompt`, `response_a`, `response_b` (sem nomes de modelo: não usar `model_a`/`model_b` como feature).
- **Métrica oficial:** log loss multiclasse sobre (`winner_model_a`, `winner_model_b`, `winner_tie`). Baseline uniforme = ln 3 ≈ 1,0986.
- **Submissão:** notebook do Kaggle sem internet, até 9 h de CPU/GPU, gerando `submission.csv` com `id` e as três probabilidades.

## Estado atual

O repositório foi criado a partir do template `datascience_template` e **o pipeline ainda roda o exemplo do Iris**. O que é específico do Iris e precisa ser trocado:

- `etl/extract.py` (carrega o Iris do scikit-learn), `etl/transform.py`
- `configs/config.yaml` (`project`, `data.table`, `data.target`, `data.features`, `display_names`, `split`, `model.params`)
- `ml/train.py` → `build_pipeline()` (hoje `StandardScaler` + `LogisticRegression`)
- `models/model.onnx` e `models/metadata.json` (regerar com `make all`)
- `tests/test_api.py`, `tests/test_etl.py` e o payload do smoke test em `.github/workflows/ci.yml`
- `pyproject.toml` ainda usa o nome de pacote `datascience-template`. Para renomear, troque `name` e rode `uv lock` (a CI usa `uv sync --locked` e falha se o lock estiver desatualizado).

O checklist do projeto está na seção **Roteiro** do README: marque os itens conforme forem concluídos.

## Decisões de projeto

- **Alvo:** uma coluna categórica com três classes (`a`, `b`, `tie`) derivada das três colunas one-hot; o `ml/evaluate.py` deve reportar log loss além das métricas de classificação do template.
- **Etapa 1 — baseline no pipeline do template:** features calculadas no ETL (tamanho de prompt e respostas, diferença e razão de tamanho, contagem de listas/títulos/código, sobreposição de palavras com o prompt) + gradient boosting/regressão logística no `Pipeline`, exportados em ONNX. É esse modelo que a API serve no início.
- **Etapa 2 — fine-tuning em PyTorch:** classificador de pares a partir de um modelo de linguagem com LoRA, treinado em GPU (Kaggle ou nuvem). Criar um grupo de dependências próprio no `pyproject.toml` (ex.: `dl = ["torch", "transformers", "peft", "accelerate"]`) para não inflar a imagem Docker, que só instala o grupo `app`.
- **Simetria A/B:** aumentar o treino trocando A e B (e invertendo o rótulo); na inferência, fazer a média com a versão trocada.
- **Textos longos:** definir uma estratégia de truncamento que preserve o fim do prompt e o começo de cada resposta.
- **Validação:** K-fold estratificado pelo rótulo; agrupar por prompt se houver prompts repetidos.
- **Servir o modelo de linguagem:** exportar com `torch.onnx.export` exige uma função de salvamento própria em `tools/model_io.py` que respeite a regra 2 (validar com `onnx.checker` e comparar com o PyTorch antes de gravar). Modelos acima de 100 MB precisam de Git LFS ou ficam fora do repositório, publicados em outro lugar.

## Regras do template (verificadas em `tests/test_project_rules.py` e na CI)

1. `etl`, `ml` e `app` importam de `tools`; `tools` não importa nenhum deles; `app` não importa `etl`, `ml`, scikit-learn nem pandas.
2. Modelos só em ONNX, salvos por `tools.model_io.save_onnx_model` (valida e compara com o modelo original). Nada de `joblib`/`pickle` em `models/`.
3. Pré-processamento que o modelo precisa na previsão fica dentro do `Pipeline`.
4. `ml/evaluate.py` mede o próprio `model.onnx`.
5. `data/` fora do git; `models/` versionado (acima de 50 MB, usar Git LFS).

## Comandos

```bash
make setup   # dependências Python (uv) e do front (npm)
make data    # baixa os dados da competição para data/raw/llm-classification-finetuning
make all     # ETL + treino + avaliação → models/model.onnx + metadata.json
make app     # API + front em http://localhost:8000
make check   # lint + testes (o mesmo que a CI)
make help    # todos os comandos
```

## Convenções

- Documentação, comentários e docstrings em português, como no resto do template.
- Antes de comitar: `make check`. Ao trocar o exemplo do Iris, rodar `make all` e comitar `models/` junto.
- A CI roda `make all` sem acesso aos dados do Kaggle: quando o extract passar a ler `data/raw`, prever um modo de amostra pequena (fixture em `tests/`) para a CI continuar verde.
- Notebooks de exploração e o notebook de submissão do Kaggle ficam em `notebooks/`; o que for definitivo vai para `etl/` ou `ml/`.
