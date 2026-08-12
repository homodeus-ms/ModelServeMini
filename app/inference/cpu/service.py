import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.model_version.schema import ModelVersionCache
from app.inference.artifact_loader import load_model_artifact
from app.inference.exceptions import (
    InferenceFailed,
    InvalidInferenceInput,
    ModelArtifactNotFound,
    InvalidInferenceInputValue
)

from app.inference.schema import InferenceRequest, InferenceResponse

logger = logging.getLogger(__name__)


def predict(db: Session, model_version: ModelVersionCache, request: InferenceRequest) -> InferenceResponse:

    #artifact_path = Path(model_version.artifact_uri)
    artifact_path = (Path(settings.model_storage_path) / model_version.artifact_uri)

    if not artifact_path.exists():
        raise ModelArtifactNotFound(model_version.artifact_uri)

    expected_columns = _get_expected_columns(model_version.input_schema)
    _validate_input_columns(request.input, expected_columns)

    ordered_input = _create_ordered_input(request.input, expected_columns)

    artifact = load_model_artifact(model_version.id, artifact_path)

    # 1건
    dataframe = pd.DataFrame([ordered_input], columns=expected_columns)

    try:
        pipeline = artifact.get("pipeline")
        predictions = pipeline.predict(dataframe)
        prediction = _to_python_value(predictions[0])

        probabilities: dict[str, float] | None = None

        # RandomForestClassifier인 경우
        if hasattr(pipeline, "predict_proba"):
            probability_result = pipeline.predict_proba(dataframe)[0]
            class_labels = pipeline.classes_

            probabilities = {
                str(class_label): float(probability)
                for class_label, probability in zip(class_labels, probability_result)
            }

    except Exception as exc:
        raise InferenceFailed(str(exc))

    return InferenceResponse(
        model_version_id=model_version.id,
        prediction=prediction,
        probabilities=probabilities
    )


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