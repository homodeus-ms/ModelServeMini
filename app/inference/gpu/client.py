import os

import httpx

from app.domain.model_version.schema import ModelVersionCache
from app.inference.schema import InferenceRequest, InferenceResponse


GPU_INFERENCE_URL = os.getenv(
    "GPU_INFERENCE_URL",
    "http://localhost:8001",
)

_client = httpx.Client(
    base_url=GPU_INFERENCE_URL,
    timeout=30.0,
)


def predict(
    model_version_cache: ModelVersionCache,
    request: InferenceRequest,
) -> InferenceResponse:

    response = _client.post(
        f"/predict",
        json={
            "model_version_id": model_version_cache.id,
            "artifact_uri": model_version_cache.artifact_uri,
            "input_schema": model_version_cache.input_schema,
            "input": request.input,
        }
    )

    response.raise_for_status()

    return InferenceResponse(**response.json())