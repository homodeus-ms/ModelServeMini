import torch
import torch.nn as nn

from torch.utils.data import DataLoader

from app.domain.training_job.enums import TrainingAlgorithm


def evaluate_model(
    algorithm: TrainingAlgorithm,
    model: nn.Module,
    test_loader: DataLoader,
) -> tuple[list, list]:

    if algorithm == TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER:
        return _evaluate_classifier(
            model,
            test_loader,
        )

    if algorithm == TrainingAlgorithm.PYTORCH_MLP_REGRESSOR:
        return _evaluate_regressor(
            model,
            test_loader,
        )

    raise ValueError(
        f"Unsupported PyTorch algorithm: {algorithm}"
    )


def _evaluate_classifier(
    model: nn.Module,
    test_loader: DataLoader,
) -> tuple[list[int], list[int]]:

    model.eval()

    y_true: list[int] = []
    y_pred: list[int] = []

    with torch.no_grad():
        for batch_features, batch_labels in test_loader:

            logits = model(batch_features)

            predictions = torch.argmax(
                logits,
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

    return y_true, y_pred


def _evaluate_regressor(
    model: nn.Module,
    test_loader: DataLoader,
) -> tuple[list[float], list[float]]:

    model.eval()

    y_true: list[float] = []
    y_pred: list[float] = []

    with torch.no_grad():
        for batch_features, batch_labels in test_loader:

            predictions = model(batch_features)

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

    return y_true, y_pred