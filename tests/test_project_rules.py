"""Regras do repositório verificadas em toda execução de testes (e na CI)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tools.config import get_path, project_root
from tools.model_io import check_models_dir

ROOT = project_root()


def test_models_dir_contains_only_onnx() -> None:
    forbidden = check_models_dir(get_path("models"))
    assert not forbidden, f"Somente .onnx (+ metadata.json) em models/. Encontrado: {forbidden}"


def _imports(package: str) -> set[str]:
    found: set[str] = set()
    for file in (ROOT / package).rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".")[0])
    return found


@pytest.mark.parametrize(
    ("package", "forbidden"),
    [
        ("tools", {"etl", "ml", "app"}),  # tools é a base: não depende de ninguém
        ("etl", {"ml", "app"}),
        ("ml", {"etl", "app"}),  # ml lê os dados publicados, não chama o ETL
        ("app", {"etl", "ml", "sklearn", "pandas", "skl2onnx", "joblib", "pickle"}),
    ],
)
def test_dependency_direction(package: str, forbidden: set[str]) -> None:
    bad = _imports(package) & forbidden
    assert not bad, f"{package}/ não pode importar {sorted(bad)}"


def test_no_pickle_or_joblib_model_saving() -> None:
    for package in ("tools", "ml", "app"):
        for file in (ROOT / package).rglob("*.py"):
            text = file.read_text(encoding="utf-8")
            assert "joblib.dump" not in text and "pickle.dump" not in text, (
                f"{file.relative_to(ROOT)}: salve modelos só com save_onnx_model"
            )


def test_data_is_not_versioned() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/*/*" in gitignore
    assert "!models/*.onnx" in gitignore


def test_root_is_repository() -> None:
    assert (ROOT / "pyproject.toml").exists()
    assert isinstance(ROOT, Path)
