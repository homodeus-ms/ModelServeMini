import torch
import torch.nn as nn

from torch.utils.data import DataLoader

from app.domain.model.enums import ModelTaskType


N_REPEATS = 5

def calculate_feature_importance(
    model: nn.Module,
    test_loader: DataLoader,
    raw_feature_columns: list[str],
    encoded_feature_columns: list[str],
    task_type: ModelTaskType,
    baseline_metric: float,
) -> list[dict[str, float | str]]:

    model.eval()

    result: dict[str, float] = {}

    for raw_feature in raw_feature_columns:

        encoded_indices = _find_encoded_indices(
            raw_feature=raw_feature,
            encoded_feature_columns=encoded_feature_columns,
        )

        if not encoded_indices:
            continue

        importance_values = []

        # permutation을 여러 번 수행
        for _ in range(N_REPEATS):

            shuffled_metric = _calculate_shuffled_metric(
                model=model,
                test_loader=test_loader,
                encoded_indices=encoded_indices,
                task_type=task_type,
            )

            if task_type == ModelTaskType.CLASSIFICATION:
                importance = baseline_metric - shuffled_metric
            else:
                # RMSE는 커질수록 성능이 나빠짐
                importance = shuffled_metric - baseline_metric

            importance_values.append(importance)

        # 여러 번 측정한 importance의 평균
        mean_importance = sum(importance_values) / len(importance_values)

        result[raw_feature] = max(float(mean_importance), 0.0)

    return sorted(
        [
            {
                "feature": feature,
                "importance": importance,
            }
            for feature, importance in result.items()
        ],
        key=lambda item: item["importance"], reverse=True,
    )


def _find_encoded_indices(
    raw_feature: str,
    encoded_feature_columns: list[str],
) -> list[int]:

    return [
        index
        for index, encoded_column in enumerate(
            encoded_feature_columns
        )
        if (
            encoded_column == raw_feature
            or encoded_column.startswith(
                f"{raw_feature}_"
            )
        )
    ]


def _calculate_shuffled_metric(
    model: nn.Module,
    test_loader: DataLoader,
    encoded_indices: list[int],
    task_type: ModelTaskType,
) -> float:

    y_true = []
    y_pred = []

    with torch.no_grad():

        for batch_features, batch_labels in test_loader:

            shuffled_features = (
                batch_features.clone()
            )

            permutation = torch.randperm(
                shuffled_features.shape[0],
                device=shuffled_features.device,
            )

            shuffled_features[
                :,
                encoded_indices,
            ] = shuffled_features[
                permutation
            ][
                :,
                encoded_indices
            ]

            predictions = model(
                shuffled_features
            )

            if task_type == ModelTaskType.CLASSIFICATION:

                predictions = torch.argmax(
                    predictions,
                    dim=1,
                )

                y_true.extend(
                    batch_labels
                    .detach()
                    .cpu()
                    .tolist()
                )

                y_pred.extend(
                    predictions
                    .detach()
                    .cpu()
                    .tolist()
                )

            else:

                y_true.extend(
                    batch_labels
                    .detach()
                    .cpu()
                    .flatten()
                    .tolist()
                )

                y_pred.extend(
                    predictions
                    .detach()
                    .cpu()
                    .flatten()
                    .tolist()
                )

    if task_type == ModelTaskType.CLASSIFICATION:
        return _calculate_accuracy(
            y_true,
            y_pred,
        )

    return _calculate_rmse(
        y_true,
        y_pred,
    )


from sklearn.metrics import (
    accuracy_score,
    mean_squared_error,
)


def _calculate_accuracy(
    y_true,
    y_pred,
) -> float:

    return float(
        accuracy_score(
            y_true,
            y_pred,
        )
    )


def _calculate_rmse(
    y_true,
    y_pred,
) -> float:

    mse = mean_squared_error(
        y_true,
        y_pred,
    )

    return float(
        mse ** 0.5
    )