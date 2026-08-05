from dataclasses import dataclass
from typing import Any


@dataclass
class TrainingResult:
    artifact_uri: str

    metrics: dict[str, Any]

    feature_columns: list[str]

    artifact_size: int | None = None

    artifact_checksum: str | None = None

    input_schema: dict[str, Any] | None = None

    feature_importances: list[dict[str, float | int | str]] | None = None
