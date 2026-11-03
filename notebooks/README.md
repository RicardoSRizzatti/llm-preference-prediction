# Notebooks

Espaço para análise exploratória (EDA) e experimentos rápidos. Não é parte do pipeline.

Convenções:

- Nome com ordem e assunto: `01_eda_inicial.ipynb`, `02_teste_features.ipynb`.
- Leia os dados pelas funções do projeto, não por caminhos soltos:

  ```python
  from tools.config import load_config
  from tools.data_io import read_processed

  df = read_processed(load_config())
  ```

- Código que se repetir ou que o pipeline precisar migra para `tools/` (funções)
  ou para `etl/` e `ml/` (etapas). Notebook não é importado por nenhum módulo.
- Limpe as saídas antes de comitar notebooks com dados sensíveis.

Para abrir: `make notebook` (Jupyter Lab) ou use o kernel `.venv` no VS Code.
