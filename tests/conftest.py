from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.config import load_config


@pytest.fixture
def config(tmp_path: Path) -> dict:
    """Config do projeto com todos os caminhos apontando para uma pasta temporária."""
    cfg = copy.deepcopy(load_config())
    cfg["paths"] = {key: str(tmp_path / key) for key in cfg["paths"]}
    return cfg
