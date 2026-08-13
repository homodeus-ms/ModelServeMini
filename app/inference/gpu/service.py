import logging
from uuid import uuid4

import cuml
import cudf
import cupy as cp
import numpy as np
import time
import torch
import torch.nn as nn

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.model.enums import ModelTaskType
from app.domain.model_version.exceptions import ModelVersionNotFound
from app.domain.model_version import repository as model_version_repository
from app.domain.model_version.model import ModelVersion
from app.gpu_scheduler.client import acquire_gpu, release_gpu
from app.gpu_scheduler.schema import GpuTaskType
from app.inference.artifact_loader import load_model_artifact
from app.inference.exceptions import (
    InferenceFailed,
    InvalidInferenceInput,
    ModelArtifactNotFound,
    InvalidInferenceInputValue
)
from app.inference.gpu.schema import GpuInferenceRequest

from app.inference.schema import InferenceRequest, InferenceResponse
from app.training.pytorch.preprocessing import prepare_inference_data

logger = logging.getLogger(__name__)

# Gpu scheduler 를 사용하기 위한 wrapper함수
def predict(request: GpuInferenceRequest) -> InferenceResponse:

    task_id = f"inference-{uuid4()}"
    gpu_acquired = False

    try:
        logger.info("requested GPU: task_id=%s", task_id)

        acquire_gpu(task_id=task_id, task_type=GpuTaskType.INFERENCE)

        gpu_acquired = True

        logger.info("GPU acquired: task_id=%s",task_id)

        return _predict(request)

    finally:
        if gpu_acquired:
            try:
                release_gpu(task_id)

                logger.info("GPU released: task_id=%s",task_id)

            except Exception:
                logger.exception("failed to release GPU: task_id=%s",task_id)


def _predict(request: GpuInferenceRequest) -> InferenceResponse:

    total_started_at = time.perf_counter()

    try:

        artifact_path = (Path(settings.model_storage_path) / request.artifact_uri)
        if not artifact_path.exists():
            raise ModelArtifactNotFound(request.artifact_uri)

        expected_columns = _get_expected_columns(request.input_schema)
        _validate_input_columns(request.input, expected_columns)

        ordered_input = _create_ordered_input(request.input, expected_columns)


        # Artifact load
        started_at = time.perf_counter()
        artifact = load_model_artifact(request.model_version_id, artifact_path)

        # TEMP : For Benchmark
        logger.info("artifact load time: %.2f ms",(time.perf_counter() - started_at) * 1000)


        # Prediction
        started_at = time.perf_counter()
        if artifact.get("framework") == "PYTORCH":
            prediction, probabilities = _predict_pytorch(
                artifact=artifact,
                input_data=ordered_input,
            )
        else:
            dataframe = cudf.DataFrame(
                [ordered_input],
                columns=expected_columns,
            )
            prediction, probabilities = _predict_by_task_type(
                artifact,
                dataframe,
            )
        logger.info(
            "predict elapsed time: %.2f ms",
            (time.perf_counter() - started_at) * 1000,
        )

        return InferenceResponse(
            model_version_id=request.model_version_id,
            prediction=prediction,
            probabilities=probabilities
        )

    finally:
        elapsed_ms = (time.perf_counter() - total_started_at) * 1000
        logger.info(f"GPU inferenced completed. {request.model_version_id}'s latency is {elapsed_ms} ms")


def _predict_by_task_type(artifact,
                          dataframe: cudf.DataFrame) -> tuple[object, dict[str, float] | None]:
    task_type = artifact.get("task_type")

    if task_type == ModelTaskType.CLASSIFICATION.value:
        return _predict_classfication(artifact, dataframe)

    if task_type == ModelTaskType.REGRESSION.value:
        prediction = _predict_regression(artifact, dataframe)
        return prediction, None

    raise InferenceFailed(f"Unsupported task type: {task_type}")


def _predict_classfication(artifact,
                           dataframe: cudf.DataFrame) -> tuple[object, dict[str, float] | None]:
    pipeline = artifact.get("pipeline")
    target_encoder = artifact.get("target_encoder")
    predictions = pipeline.predict(dataframe)
    prediction = _to_python_value(predictions[0])

    class_labels = pipeline.classes_

    if target_encoder is not None:
        predictions_cpu = cp.asnumpy(predictions)
        decoded_predictions = target_encoder.inverse_transform(predictions_cpu)
        prediction = _to_python_value(decoded_predictions[0])
        class_labels = target_encoder.inverse_transform(np.asarray(class_labels))

    probabilities = None

    # RandomForestClassifier인 경우
    if hasattr(pipeline, "predict_proba"):
        probability_result = pipeline.predict_proba(dataframe)[0]
        probabilities = {
            str(class_label): float(probability)
            for class_label, probability in zip(
                class_labels,
                probability_result,
            )
        }

    return prediction, probabilities

def _predict_regression(artifact,
                        dataframe: cudf.DataFrame) -> tuple[object, dict[str, float] | None]:

    pipeline = artifact.get("pipeline")
    predictions = pipeline.predict(dataframe)
    return _to_python_value(predictions[0])

def _predict_pytorch(
    artifact: dict,
    input_data: dict[str, Any],
) -> tuple[
    object,
    dict[str, float] | None,
]:

    model = artifact["model"]

    input_tensor = prepare_inference_data(
        input_data=input_data,
        encoded_feature_columns=artifact[
            "encoded_feature_columns"
        ],
    )

    task_type = artifact.get(
        "task_type"
    )

    if task_type == ModelTaskType.CLASSIFICATION.value:
        return _predict_pytorch_classification(
            artifact=artifact,
            model=model,
            input_tensor=input_tensor,
        )

    if task_type == ModelTaskType.REGRESSION.value:
        return _predict_pytorch_regression(
            model=model,
            input_tensor=input_tensor,
        )

    raise InferenceFailed(
        f"Unsupported PyTorch task type: {task_type}"
    )


def _predict_pytorch_classification(
    artifact: dict,
    model: nn.Module,
    input_tensor: torch.Tensor,
) -> tuple[
    object,
    dict[str, float],
]:

    with torch.no_grad():

        logits = model(
            input_tensor
        )

        probabilities_tensor = torch.softmax(
            logits,
            dim=1,
        )

        class_index = torch.argmax(
            probabilities_tensor,
            dim=1,
        ).item()

    target_categories = artifact[
        "target_categories"
    ]

    prediction = target_categories[
        class_index
    ]

    probability_values = (
        probabilities_tensor[0]
        .detach()
        .cpu()
        .tolist()
    )

    probabilities = {
        str(category): float(probability)
        for category, probability in zip(
            target_categories,
            probability_values,
        )
    }

    return prediction, probabilities


def _predict_pytorch_regression(
    model: nn.Module,
    input_tensor: torch.Tensor,
) -> tuple[
    float,
    None,
]:

    with torch.no_grad():

        prediction_tensor = model(
            input_tensor
        )

    prediction = float(
        prediction_tensor
        .detach()
        .cpu()
        .item()
    )

    return prediction, None



def _get_expected_columns(input_schema: dict[str, Any] | None) -> list[str]:

    if input_schema is None:
        raise InvalidInferenceInput()

    columns = input_schema.get("columns")

    if not isinstance(columns, list):
        raise InvalidInferenceInput()

    expected_columns: list[str] = []

    for column in columns:
        if not isinstance(column, dict):
            raise InvalidInferenceInput()

        name = column.get("name")

        if not isinstance(name, str):
            raise InvalidInferenceInput()

        expected_columns.append(name)

    return expected_columns


def _validate_input_columns(
    input_data: dict[str, Any],
    expected_columns: list[str]
) -> None:
    input_columns = set(input_data.keys())
    expected_column_set = set(expected_columns)

    missing_columns = sorted(
        expected_column_set - input_columns
    )

    extra_columns = sorted(
        input_columns - expected_column_set
    )

    logger.info(
        "expected_columns=%s",
        expected_columns,
    )

    logger.info(
        "input_columns=%s",
        list(input_data.keys()),
    )

    logger.info(
        "missing_columns=%s extra_columns=%s",
        missing_columns,
        extra_columns,
    )


    if missing_columns or extra_columns:
        raise InvalidInferenceInput(
            missing_columns,
            extra_columns
        )


def _create_ordered_input(input_data: dict[str, Any], expected_columns: list[str]) -> dict[str, int | float]:

    ordered_input: dict[str, Any] = {}

    for column in expected_columns:

        value = input_data[column]

        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise InvalidInferenceInputValue(
                column=column,
                value_type=type(value).__name__
            )

        ordered_input[column] = value

    return ordered_input


def _to_python_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()

    return value