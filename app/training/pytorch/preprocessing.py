import cudf
import torch

from typing import Any
from cuml.model_selection import train_test_split
from torch.utils.data import TensorDataset


def _encode_features(
    features: cudf.DataFrame,
) -> tuple[cudf.DataFrame, list[str]]:

    encoded_features = cudf.get_dummies(
        features,
        dummy_na=False,
    )

    encoded_feature_columns = list(
        encoded_features.columns
    )

    return (
        encoded_features,
        encoded_feature_columns,
    )


def prepare_classification_data(
    features: cudf.DataFrame,
    target: cudf.Series,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[
    TensorDataset,
    TensorDataset,
    int,
    int,
    list[str],
    list,
]:

    (
        encoded_features,
        encoded_feature_columns,
    ) = _encode_features(
        features
    )

    target_codes, target_categories = (
        target.factorize()
    )

    target_category_list = (
        target_categories
        .to_arrow()
        .to_pylist()
    )

    x_train, x_test, y_train, y_test = (
        train_test_split(
            encoded_features,
            target_codes,
            test_size=test_size,
            random_state=random_state,
        )
    )

    x_train_tensor = torch.as_tensor(
        x_train.to_cupy(),
        device="cuda",
        dtype=torch.float32,
    )

    x_test_tensor = torch.as_tensor(
        x_test.to_cupy(),
        device="cuda",
        dtype=torch.float32,
    )

    y_train_tensor = torch.as_tensor(
        y_train,
        device="cuda",
        dtype=torch.long,
    )

    y_test_tensor = torch.as_tensor(
        y_test,
        device="cuda",
        dtype=torch.long,
    )

    train_dataset = TensorDataset(
        x_train_tensor,
        y_train_tensor,
    )

    test_dataset = TensorDataset(
        x_test_tensor,
        y_test_tensor,
    )

    return (
        train_dataset,
        test_dataset,
        x_train_tensor.shape[1],
        len(target_category_list),
        encoded_feature_columns,
        target_category_list,
    )


def prepare_regression_data(
    features: cudf.DataFrame,
    target: cudf.Series,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[
    TensorDataset,
    TensorDataset,
    int,
    list[str],
]:

    (
        encoded_features,
        encoded_feature_columns,
    ) = _encode_features(
        features
    )

    x_train, x_test, y_train, y_test = (
        train_test_split(
            encoded_features,
            target,
            test_size=test_size,
            random_state=random_state,
        )
    )

    x_train_tensor = torch.as_tensor(
        x_train.to_cupy(),
        device="cuda",
        dtype=torch.float32,
    )

    x_test_tensor = torch.as_tensor(
        x_test.to_cupy(),
        device="cuda",
        dtype=torch.float32,
    )

    y_train_tensor = torch.as_tensor(
        y_train.to_cupy(),
        device="cuda",
        dtype=torch.float32,
    ).reshape(-1, 1)

    y_test_tensor = torch.as_tensor(
        y_test.to_cupy(),
        device="cuda",
        dtype=torch.float32,
    ).reshape(-1, 1)

    train_dataset = TensorDataset(
        x_train_tensor,
        y_train_tensor,
    )

    test_dataset = TensorDataset(
        x_test_tensor,
        y_test_tensor,
    )

    return (
        train_dataset,
        test_dataset,
        x_train_tensor.shape[1],
        encoded_feature_columns,
    )


def prepare_inference_data(
    input_data: dict[str, Any],
    encoded_feature_columns: list[str],
) -> torch.Tensor:

    dataframe = cudf.DataFrame(
        [input_data]
    )

    encoded_dataframe = cudf.get_dummies(
        dataframe,
        dummy_na=False,
    )

    for column in encoded_feature_columns:

        if column not in encoded_dataframe.columns:
            encoded_dataframe[column] = 0

    encoded_dataframe = encoded_dataframe[
        encoded_feature_columns
    ]

    return torch.as_tensor(
        encoded_dataframe.to_cupy(),
        device="cuda",
        dtype=torch.float32,
    )