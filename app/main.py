import asyncio
import os
import threading
from contextlib import asynccontextmanager

import app.db.models
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
from app.sse.router import router as sse_router
from app.domain.training_batch.router import router as training_batch_router

import app.core.logging

from app.redis.subscriber import run_batch_event_subscriber


@asynccontextmanager
async def lifespan(app: FastAPI):

    loop = asyncio.get_running_loop()

    stop_event = threading.Event()

    subscriber_thread = threading.Thread(
        target=run_batch_event_subscriber,
        kwargs={
            "loop": loop,
            "stop_event": stop_event,
        },
        daemon=True,
    )

    subscriber_thread.start()

    # 여기서의 yield는 워커스레드 실행중 / 종료 경계임
    yield

    stop_event.set()
    subscriber_thread.join(timeout=2)


app = FastAPI(
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(member_router)
app.include_router(dataset_router)
app.include_router(dataset_version_router)
app.include_router(model_router)
app.include_router(training_job_router)
app.include_router(model_version_router)
app.include_router(training_router)
app.include_router(inference_router)
app.include_router(sse_router)
app.include_router(training_batch_router)