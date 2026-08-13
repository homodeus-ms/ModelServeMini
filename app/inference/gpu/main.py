from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.inference.gpu.schema import GpuInferenceRequest
from app.inference.model_cache import clear_model_artifact
from app.inference.schema import InferenceRequest, InferenceResponse
from app.inference.gpu import service
import app.core.logging

app = FastAPI()


@app.post("/predict", response_model=InferenceResponse)
def predict(request: GpuInferenceRequest) -> InferenceResponse:

    return service.predict(request)

@app.delete("/inference/model_versions/model_cache")
def clear_model_cache():

    clear_model_artifact()