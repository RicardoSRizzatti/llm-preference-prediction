"""Leitura do configs/config.yaml e resolução de caminhos."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path("configs") / "config.yaml"


def project_root() -> Path:
    """Raiz do repositório: a pasta que contém o pyproject.toml.

    Pode ser forçada pela variável PROJECT_ROOT (útil no Docker).
    """
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()

    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise FileNotFoundError("Não encontrei a raiz do projeto (pyproject.toml).")


@lru_cache(maxsize=4)
def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Carrega a configuração. Ordem: argumento > CONFIG_PATH > configs/config.yaml."""
    raw = path or os.getenv("CONFIG_PATH") or DEFAULT_CONFIG
    config_path = Path(raw)
    if not config_path.is_absolute():
        config_path = project_root() / config_path
    return _load(config_path)


def get_path(key: str, config: dict[str, Any] | None = None, create: bool = False) -> Path:
    """Caminho absoluto de uma entrada de `paths` (raw, interim, processed, split, models)."""
    config = config or load_config()
    try:
        relative = config["paths"][key]
    except KeyError as exc:
        raise KeyError(f"Caminho '{key}' não definido em paths no config.yaml") from exc

    path = Path(relative)
    if not path.is_absolute():
        path = project_root() / path
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path
