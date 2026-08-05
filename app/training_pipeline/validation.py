import pandas as pd


def validate_dataframe(dataframe: pd.DataFrame, target_column: str) -> None:

    if dataframe.empty:
        raise ValueError("Dataset is empty")

    if target_column not in dataframe.columns:
        raise ValueError(
            f"Target column not found: {target_column}"
        )

    if dataframe[target_column].isnull().any():
        raise ValueError(
            "Target column contains null values"
        )


def validate_feature_columns(
    dataframe: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
) -> None:

    if not feature_columns:
        raise ValueError(
            "feature_columns is required"
        )

    if target_column in feature_columns:
        raise ValueError(
            "Target column cannot be included in feature_columns"
        )

    if len(feature_columns) != len(set(feature_columns)):
        raise ValueError(
            "feature_columns contains duplicates"
        )

    missing_columns = [
        column
        for column in feature_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Feature columns not found: {missing_columns}"
        )


def validate_features(features: pd.DataFrame) -> None:

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