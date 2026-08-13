from typing import Any

from pydantic import BaseModel


class GpuInferenceRequest(BaseModel):
    model_version_id: int
    artifact_uri: str
    input_schema: dict[str, Any]
    input: dict[str, Any]