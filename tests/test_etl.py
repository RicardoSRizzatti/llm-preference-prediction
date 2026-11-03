from __future__ import annotations

import pandas as pd

from etl.transform import transform


def test_transform_standardizes_columns_and_target(config: dict) -> None:
    raw = pd.DataFrame(
        {
            "sepal length (cm)": [5.1, 5.1, 7.0, None],
            "sepal width (cm)": [3.5, 3.5, 3.2, 3.0],
            "petal length (cm)": [1.4, 1.4, 4.7, 1.0],
            "petal width (cm)": [0.2, 0.2, 1.4, 0.1],
            "target": [0, 0, 1, 2],
        }
    )
    df = transform(raw, config)

    assert list(df.columns) == [*config["data"]["features"], config["data"]["target"]]
    assert len(df) == 2  # uma duplicada e uma com nulo removidas
    assert df[config["data"]["target"]].tolist() == ["setosa", "versicolor"]
    assert all(df[f].dtype == "float64" for f in config["data"]["features"])
