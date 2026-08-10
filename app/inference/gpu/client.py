import httpx

from app.inference.schema import InferenceRequest, InferenceResponse


GPU_INFERENCE_URL = "http://localhost:8001"

_client = httpx.Client(
    base_url=GPU_INFERENCE_URL,
    timeout=30.0,
)


def predict(
    model_version_id: int,
    request: InferenceRequest,
) -> InferenceResponse:

    response = _client.post(
        f"/predict/{model_version_id}",
        json=request.model_dump(),
    )

    response.raise_for_status()

    return InferenceResponse(**response.json())