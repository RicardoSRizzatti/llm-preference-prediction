"""Informações do git para rastrear qual código gerou cada modelo."""

from __future__ import annotations

import subprocess

from tools.config import project_root


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=project_root(), capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def current_commit() -> dict[str, str | bool | None]:
    """Commit atual e se havia alterações não comitadas (dirty) no código ao treinar.

    A pasta models/ fica de fora: ela é justamente o que o treino está gerando.
    """
    status = _git("status", "--porcelain", "--", ".", ":(exclude)models")
    return {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "dirty": bool(status) if status is not None else None,
    }
