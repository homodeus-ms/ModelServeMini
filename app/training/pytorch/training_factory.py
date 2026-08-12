from dataclasses import dataclass

import cudf
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from app.domain.training_job.enums import TrainingAlgorithm
from app.training.pytorch.model import (
    MLPClassifier,
    MLPRegressor,
)
from app.training.pytorch.preprocessing import (
    prepare_classification_data,
    prepare_regression_data,
)


@dataclass
class TrainingComponents:

    model: nn.Module
    loss_fn: nn.Module

    train_dataset: TensorDataset
    test_dataset: TensorDataset

    input_size: int

    encoded_feature_columns: list[str]

    num_classes: int | None = None
    target_categories: list | None = None


def create_training_components(
    algorithm: TrainingAlgorithm,
    features: cudf.DataFrame,
    target: cudf.Series,
    hidden_size: int,
    test_size: float,
    random_state: int,
) -> TrainingComponents:

    if algorithm == TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER:
        return _create_classifier_components(
            features=features,
            target=target,
            hidden_size=hidden_size,
            test_size=test_size,
            random_state=random_state,
        )

    if algorithm == TrainingAlgorithm.PYTORCH_MLP_REGRESSOR:
        return _create_regressor_components(
            features=features,
            target=target,
            hidden_size=hidden_size,
            test_size=test_size,
            random_state=random_state,
        )

    raise ValueError(
        f"Unsupported PyTorch algorithm: {algorithm}"
    )


def _create_classifier_components(
    features: cudf.DataFrame,
    target: cudf.Series,
    hidden_size: int,
    test_size: float,
    random_state: int,
) -> TrainingComponents:

    (
        train_dataset,
        test_dataset,
        input_size,
        num_classes,
        encoded_feature_columns,
        target_categories,
    ) = prepare_classification_data(
        features=features,
        target=target,
        test_size=test_size,
        random_state=random_state,
    )

    model = MLPClassifier(
        input_size=input_size,
        hidden_size=hidden_size,
        num_classes=num_classes,
    ).to("cuda")

    return TrainingComponents(
        train_dataset=train_dataset,
        test_dataset=test_dataset,
        model=model,
        loss_fn=nn.CrossEntropyLoss(),
        input_size=input_size,
        encoded_feature_columns=encoded_feature_columns,
        num_classes=num_classes,
        target_categories=target_categories,
    )


def _create_regressor_components(
    features: cudf.DataFrame,
    target: cudf.Series,
    hidden_size: int,
    test_size: float,
    random_state: int,
) -> TrainingComponents:

    (
        train_dataset,
        test_dataset,
        input_size,
        encoded_feature_columns,
    ) = prepare_regression_data(
        features=features,
        target=target,
        test_size=test_size,
        random_state=random_state,
    )

    model = MLPRegressor(
        input_size=input_size,
        hidden_size=hidden_size,
    ).to("cuda")

    return TrainingComponents(
        train_dataset=train_dataset,
        test_dataset=test_dataset,
        model=model,
        loss_fn=nn.MSELoss(),
        input_size=input_size,
        encoded_feature_columns=encoded_feature_columns,
    )