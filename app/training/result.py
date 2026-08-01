from dataclasses import dataclass
from typing import Any


@dataclass
class TrainingResult:
    artifact_uri: str

    metrics: dict[str, Any]

    artifact_size: int | None = None

    artifact_checksum: str | None = None

    input_schema: dict[str, Any] | None = None