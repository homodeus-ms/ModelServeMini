import pandas as pd

def validate_cpu_features(features: pd.DataFrame) -> None:

    if features.empty:
        raise ValueError(
            "Dataset has no feature columns"
        )

    unsupported_columns = [
        column
        for column in features.columns
        if not (
                pd.api.types.is_numeric_dtype(features[column])
                or pd.api.types.is_string_dtype(features[column])
                or isinstance(
            features[column].dtype,
            pd.CategoricalDtype
        )
        )
    ]

    if unsupported_columns:
        raise ValueError(
            f"Unsupported feature columns: {unsupported_columns}"
        )