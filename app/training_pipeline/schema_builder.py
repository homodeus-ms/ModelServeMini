from typing import Any

import pandas as pd


def create_input_schema(features: pd.DataFrame) -> dict[str, Any]:
    return {
        "columns": [
            {
                "name": column,
                "dtype": str(features[column].dtype),
            }
            for column in features.columns
        ]
    }