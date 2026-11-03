"""Leitura e escrita de tabelas.

- Etapas intermediárias (raw, interim, split) são sempre locais, em parquet.
- Os dados processados vão para o destino definido em `load.destination`:
  local (padrão), bigquery ou gcs. Quem lê (ml/split.py) usa a mesma função,
  então sempre encontra os dados onde o load gravou.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

import pandas as pd

from tools.config import get_path, load_config

DESTINATIONS = ("local", "bigquery", "gcs")


# --------------------------------------------------------------------------- local
def local_path(name: str, stage: str, config: dict[str, Any] | None = None) -> Path:
    return get_path(stage, config) / f"{name}.parquet"


def write_local(
    df: pd.DataFrame, name: str, stage: str, config: dict[str, Any] | None = None
) -> Path:
    """Grava `df` em <paths.stage>/<name>.parquet."""
    get_path(stage, config, create=True)
    path = local_path(name, stage, config)
    df.to_parquet(path, index=False)
    return path


def read_local(name: str, stage: str, config: dict[str, Any] | None = None) -> pd.DataFrame:
    path = local_path(name, stage, config)
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe. Rode a etapa anterior do pipeline.")
    return pd.read_parquet(path)


# ----------------------------------------------------------------------- processed
def destination(config: dict[str, Any] | None = None) -> str:
    config = config or load_config()
    dest = config.get("load", {}).get("destination", "local")
    if dest not in DESTINATIONS:
        raise ValueError(f"load.destination='{dest}' inválido. Use um de {DESTINATIONS}.")
    return dest


def write_processed(df: pd.DataFrame, config: dict[str, Any] | None = None) -> str:
    """Publica a tabela processada no destino configurado. Retorna onde gravou."""
    config = config or load_config()
    name = config["data"]["table"]
    dest = destination(config)

    if dest == "local":
        return str(write_local(df, name, "processed", config))
    if dest == "bigquery":
        return _write_bigquery(df, config)
    return _write_gcs(df, config)


def read_processed(config: dict[str, Any] | None = None) -> pd.DataFrame:
    """Lê a tabela processada do destino configurado."""
    config = config or load_config()
    name = config["data"]["table"]
    dest = destination(config)

    if dest == "local":
        return read_local(name, "processed", config)
    if dest == "bigquery":
        return _read_bigquery(config)
    return _read_gcs(config)


# ------------------------------------------------------------------------ bigquery
def _bigquery_module():
    try:
        from google.cloud import bigquery
    except ImportError as exc:  # pragma: no cover - depende do ambiente
        raise ImportError("Instale o grupo gcp: make setup-gcp") from exc
    return bigquery


def _bq_settings(config: dict[str, Any]) -> tuple[str, str]:
    bq = config["load"]["bigquery"]
    project = bq.get("project") or os.getenv("GCP_PROJECT")
    if not project:
        raise ValueError("Defina load.bigquery.project no config.yaml ou GCP_PROJECT no .env.")
    table_id = f"{project}.{bq['dataset']}.{config['data']['table']}"
    return project, table_id


def _write_bigquery(df: pd.DataFrame, config: dict[str, Any]) -> str:
    project, table_id = _bq_settings(config)  # valida a config antes de exigir o pacote
    bigquery = _bigquery_module()
    client = bigquery.Client(project=project)
    dataset_id = table_id.rsplit(".", 1)[0]
    client.create_dataset(dataset_id, exists_ok=True)

    job_config = bigquery.LoadJobConfig(
        write_disposition=config["load"]["bigquery"].get("write_disposition", "WRITE_TRUNCATE")
    )
    client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
    return f"bigquery://{table_id}"


def _read_bigquery(config: dict[str, Any]) -> pd.DataFrame:
    project, table_id = _bq_settings(config)
    client = _bigquery_module().Client(project=project)
    # list_rows lê a tabela sem disparar uma query (sem custo de processamento).
    return client.list_rows(table_id).to_dataframe(create_bqstorage_client=False)


# ----------------------------------------------------------------------------- gcs
def _storage_client(project: str | None):
    try:
        from google.cloud import storage
    except ImportError as exc:  # pragma: no cover - depende do ambiente
        raise ImportError("Instale o grupo gcp: make setup-gcp") from exc
    return storage.Client(project=project)


def _gcs_settings(config: dict[str, Any]) -> tuple[str, str]:
    gcs = config["load"]["gcs"]
    bucket = gcs.get("bucket") or os.getenv("GCS_BUCKET")
    if not bucket:
        raise ValueError("Defina load.gcs.bucket no config.yaml ou GCS_BUCKET no .env.")
    prefix = (gcs.get("prefix") or "").strip("/")
    blob_name = "/".join(
        p for p in (prefix, "processed", f"{config['data']['table']}.parquet") if p
    )
    return bucket, blob_name


def _write_gcs(df: pd.DataFrame, config: dict[str, Any]) -> str:
    bucket_name, blob_name = _gcs_settings(config)
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)

    client = _storage_client(os.getenv("GCP_PROJECT"))
    blob = client.bucket(bucket_name).blob(blob_name)
    blob.upload_from_string(buffer.getvalue(), content_type="application/octet-stream")
    return f"gs://{bucket_name}/{blob_name}"


def _read_gcs(config: dict[str, Any]) -> pd.DataFrame:
    bucket_name, blob_name = _gcs_settings(config)
    client = _storage_client(os.getenv("GCP_PROJECT"))
    data = client.bucket(bucket_name).blob(blob_name).download_as_bytes()
    return pd.read_parquet(io.BytesIO(data))
