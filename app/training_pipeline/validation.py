import logging
import pandas as pd

logger = logging.getLogger(__name__)

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



