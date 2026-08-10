import logging
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

MAX_CACHE_SIZE = 3

_model_cache_LRU: OrderedDict[int, Any] = OrderedDict()

def get_model_artifact(model_version_id: int) -> Any | None:
    artifact = _model_cache_LRU.get(model_version_id)
    if artifact is None: return None

    # 최근 사용된 모델을 마지막으로 이동
    _model_cache_LRU.move_to_end(model_version_id)
    return artifact

def set_model_artifact(model_version_id: int, artifact: Any) -> None:
    _model_cache_LRU[model_version_id] = artifact
    _model_cache_LRU.move_to_end(model_version_id)

    if len(_model_cache_LRU) > MAX_CACHE_SIZE:
        _model_cache_LRU.popitem(last=False)

def remove_model_artifact(model_version_id: int) -> None:
    _model_cache_LRU.pop(model_version_id, None)

def clear_model_artifact() -> None:
    _model_cache_LRU.clear()

