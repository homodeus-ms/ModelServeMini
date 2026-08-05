from fastapi import FastAPI

from app.core.config import settings
from app.core.handlers import register_exception_handlers
from app.domain.dataset.router import router as dataset_router
from app.domain.member.router import router as member_router
from app.domain.dataset_version.router import router as dataset_version_router
from app.domain.model.router import router as model_router
from app.domain.training_job.router import router as training_job_router
from app.domain.model_version.router import router as model_version_router
from app.training.router import router as training_router
from app.inference.router import router as inference_router


app = FastAPI()

register_exception_handlers(app)

app.include_router(member_router)
app.include_router(dataset_router)
app.include_router(dataset_version_router)
app.include_router(model_router)
app.include_router(training_job_router)
app.include_router(model_version_router)
app.include_router(training_router)
app.include_router(inference_router)
