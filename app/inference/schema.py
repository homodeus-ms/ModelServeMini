from typing import Any

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    model_version_id: int = Field(gt=0)
    input: dict[str, Any]


class InferenceResponse(BaseModel):
    model_version_id: int
    prediction: Any
    probabilities: list[float] | None = None