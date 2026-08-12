from typing import Any

import torch.nn as nn

from app.domain.model.enums import ModelTaskType
from app.domain.training_job.enums import TrainingAlgorithm
from app.training.pytorch.model import (
    MLPClassifier,
    MLPRegressor,
)


def create_pytorch_artifact(
    algorithm: TrainingAlgorithm,
    model: nn.Module,
    input_size: int,
    hidden_size: int,
    raw_feature_columns: list[str],
    encoded_feature_columns: list[str],
    num_classes: int | None,
    target_categories: list | None,
) -> dict:

    artifact: dict[str, Any] = {
        "framework": "PYTORCH",
        "model_state_dict": model.state_dict(),

        "input_size": input_size,
        "hidden_size": hidden_size,

        "raw_feature_columns": raw_feature_columns,
        "encoded_feature_columns": encoded_feature_columns,
    }

    if algorithm == TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER:
        artifact.update(
            {
                "num_classes": num_classes,
                "target_categories": target_categories,
                "task_type": ModelTaskType.CLASSIFICATION.value,
            }
        )

        return artifact

    if algorithm == TrainingAlgorithm.PYTORCH_MLP_REGRESSOR:
        artifact.update(
            {
                "task_type": ModelTaskType.REGRESSION.value,
            }
        )

        return artifact

    raise ValueError(
        f"Unsupported PyTorch algorithm: {algorithm}"
    )


def restore_model(
    artifact: dict,
) -> nn.Module:

    task_type = artifact.get(
        "task_type"
    )

    input_size = artifact[
        "input_size"
    ]

    hidden_size = artifact[
        "hidden_size"
    ]

    if task_type == ModelTaskType.CLASSIFICATION.value:

        model = MLPClassifier(
            input_size=input_size,
            hidden_size=hidden_size,
            num_classes=artifact[
                "num_classes"
            ],
        )

    elif task_type == ModelTaskType.REGRESSION.value:

        model = MLPRegressor(
            input_size=input_size,
            hidden_size=hidden_size,
        )

    else:
        raise ValueError(
            f"Unsupported PyTorch task type: {task_type}"
        )

    model = model.to("cuda")

    model.load_state_dict(
        artifact[
            "model_state_dict"
        ]
    )

    model.eval()

    return model