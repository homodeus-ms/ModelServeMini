import json
from typing import Any

from app.domain.model_version.schema import ModelVersionCache
from app.redis.client import redis_client
from app.redis.consts import MODEL_VERSION_KEY_PREFIX, MODEL_KEY_PREFIX


def get_deployed_model_version_redis(model_id: int) -> ModelVersionCache | None:

    key = (f"{MODEL_KEY_PREFIX}:" f"{model_id}")

    data = redis_client.get(key)

    if data is None:
        return None

    return ModelVersionCache.model_validate(json.loads(data))


def set_deployed_model_version_redis(model_id: int, value: ModelVersionCache) -> None:

    key = (f"{MODEL_KEY_PREFIX}:" f"{model_id}")

    redis_client.set(key, value.model_dump_json(), ex=3600)

