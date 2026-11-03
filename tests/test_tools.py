from __future__ import annotations

import io
from types import SimpleNamespace

import pandas as pd
import pytest

from tools import data_io
from tools.frames import feature_stats, require_columns, snake_case, snake_case_columns


# --------------------------------------------------------------------- frames
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("sepal length (cm)", "sepal_length"),
        ("Petal Width [mm]", "petal_width"),
        ("ClientID", "client_id"),
        ("  valor-total R$ ", "valor_total_r"),
    ],
)
def test_snake_case(raw: str, expected: str) -> None:
    assert snake_case(raw) == expected


def test_snake_case_columns_detects_collisions() -> None:
    with pytest.raises(ValueError):
        snake_case_columns(pd.DataFrame(columns=["a b", "a_b"]))


def test_require_columns() -> None:
    with pytest.raises(KeyError, match="faltando|ausentes"):
        require_columns(pd.DataFrame({"a": [1]}), ["a", "b"])


def test_feature_stats() -> None:
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "cor": ["azul", "verde", "azul"]})
    stats = feature_stats(df, ["x", "cor"])
    assert stats["x"]["type"] == "numeric"
    assert stats["x"]["min"] == 1.0 and stats["x"]["max"] == 3.0
    assert stats["cor"] == {"type": "categorical", "categories": ["azul", "verde"]}


# -------------------------------------------------------------------- data_io
@pytest.fixture
def df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1.0, 2.0], "b": ["x", "y"]})


def test_local_roundtrip(config: dict, df: pd.DataFrame) -> None:
    path = data_io.write_local(df, "tabela", "raw", config)
    assert path.exists()
    pd.testing.assert_frame_equal(data_io.read_local("tabela", "raw", config), df)


def test_processed_local_is_default(config: dict, df: pd.DataFrame) -> None:
    location = data_io.write_processed(df, config)
    assert location.endswith(f"{config['data']['table']}.parquet")
    pd.testing.assert_frame_equal(data_io.read_processed(config), df)


def test_invalid_destination(config: dict, df: pd.DataFrame) -> None:
    config["load"]["destination"] = "ftp"
    with pytest.raises(ValueError, match="inválido"):
        data_io.write_processed(df, config)


def test_gcs_roundtrip_with_fake_client(config: dict, df: pd.DataFrame, monkeypatch) -> None:
    storage: dict[str, bytes] = {}

    class FakeBlob:
        def __init__(self, name: str) -> None:
            self.name = name

        def upload_from_string(self, data: bytes, content_type: str) -> None:
            storage[self.name] = data

        def download_as_bytes(self) -> bytes:
            return storage[self.name]

    fake_client = SimpleNamespace(bucket=lambda _: SimpleNamespace(blob=FakeBlob))
    monkeypatch.setattr(data_io, "_storage_client", lambda project: fake_client)
    config["load"].update(destination="gcs", gcs={"bucket": "meu-bucket", "prefix": "proj"})

    location = data_io.write_processed(df, config)
    assert location == f"gs://meu-bucket/proj/processed/{config['data']['table']}.parquet"
    pd.testing.assert_frame_equal(data_io.read_processed(config), df)


def test_bigquery_write_with_fake_module(config: dict, df: pd.DataFrame, monkeypatch) -> None:
    calls: dict = {}

    class FakeClient:
        def __init__(self, project: str) -> None:
            calls["project"] = project

        def create_dataset(self, dataset_id: str, exists_ok: bool) -> None:
            calls["dataset"] = dataset_id

        def load_table_from_dataframe(self, frame, table_id, job_config):
            calls["table"], calls["rows"] = table_id, len(frame)
            return SimpleNamespace(result=lambda: None)

    fake_module = SimpleNamespace(Client=FakeClient, LoadJobConfig=lambda **kw: kw)
    monkeypatch.setattr(data_io, "_bigquery_module", lambda: fake_module)
    config["load"]["destination"] = "bigquery"
    config["load"]["bigquery"].update(project="meu-projeto", dataset="ds")

    location = data_io.write_processed(df, config)
    table = config["data"]["table"]
    assert location == f"bigquery://meu-projeto.ds.{table}"
    assert calls == {
        "project": "meu-projeto",
        "dataset": "meu-projeto.ds",
        "table": f"meu-projeto.ds.{table}",
        "rows": 2,
    }


def test_bigquery_requires_project(config: dict, df: pd.DataFrame, monkeypatch) -> None:
    monkeypatch.delenv("GCP_PROJECT", raising=False)
    config["load"]["destination"] = "bigquery"
    config["load"]["bigquery"]["project"] = None
    with pytest.raises(ValueError, match="GCP_PROJECT"):
        data_io.write_processed(df, config)


def test_parquet_buffer_helper_is_stdlib_io() -> None:
    # Garante que tools.data_io usa o io da biblioteca padrão (nome do módulo não conflita).
    assert data_io.io is io
