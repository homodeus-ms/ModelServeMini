from typing import Any

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    input: dict[str, Any]


class InferenceResponse(BaseModel):
    model_version_id: int
    prediction: Any
    probabilities: dict[str, float] | None = None