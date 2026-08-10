import logging
from pathlib import Path

import joblib

from app.inference import model_cache
from app.inference.exceptions import ModelArtifactNotFound

logger = logging.getLogger(__name__)

def load_model_artifact(model_version_id: int, artifact_path: Path):

    cached = model_cache.get_model_artifact(model_version_id)

    if cached is not None:
        logger.info(f"Artifact cache Hit. model_version : {model_version_id}")
        return cached

    logger.info(f"Artifact cache Miss. model_version : {model_version_id}")

    artifact = joblib.load(artifact_path)
    if artifact is None:
        raise ModelArtifactNotFound(str(artifact_path))

    model_cache.set_model_artifact(model_version_id, artifact)

    return artifact
