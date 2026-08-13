import logging
import time
from sqlalchemy.orm import Session

from app.domain.model_version.exceptions import ModelVersionNotFound
from app.domain.model_version.mapper import model_version_to_cache_dto
from app.domain.model_version.schema import ModelVersionCache
from app.inference.exceptions import DeployVersionNotFound
from app.inference.schema import InferenceRequest, InferenceResponse
from app.domain.model_version import repository as model_version_repository
from app.inference.cpu import service as cpu_service
from app.inference.gpu import client as gpu_client
from app.redis.cache import get_deployed_model_version_redis, set_deployed_model_version_redis
from app.training.algorithm_registry import GPU_ALGORITHMS

logger = logging.getLogger(__name__)

# 현재 Deploy Version에 의한 추론 (redis 사용)
def predict_by_model(db: Session, model_id, request: InferenceRequest) -> InferenceResponse:

    started_at = time.perf_counter()

    try:
        cached = get_deployed_model_version_redis(model_id)
        if cached is not None:
            return _call_service(db, cached, request)

        deploy_version = model_version_repository.find_deploy_version_by_id(db, model_id)
        if deploy_version is None:
            raise DeployVersionNotFound(model_id)

        to_cached = model_version_to_cache_dto(deploy_version)

        set_deployed_model_version_redis(model_id, to_cached)

        return _call_service(db, to_cached, request)

    finally:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(f"inference completed. {model_id}'s latency is {elapsed_ms} ms")

# 사용자가 직접 model_version을 지정해서 추론
def predict_by_model_version(db: Session, model_version_id: int,
                             request: InferenceRequest) -> InferenceResponse:

    model_version = model_version_repository.find_by_id(db, model_version_id)
    if model_version is None:
        raise ModelVersionNotFound(model_version_id)
    model_version_cache = model_version_to_cache_dto(model_version)

    return _call_service(db, model_version_cache, request)


def _call_service(db: Session, model_version_cache: ModelVersionCache, request: InferenceRequest) -> InferenceResponse:

    if model_version_cache.algorithm in GPU_ALGORITHMS:
        return gpu_client.predict(model_version_cache, request)

    return cpu_service.predict(db, model_version_cache, request)