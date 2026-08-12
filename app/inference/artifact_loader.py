import logging
from pathlib import Path

import joblib
import torch

from app.inference import model_cache
from app.inference.exceptions import ModelArtifactNotFound
from app.training.pytorch.artifact import restore_model

logger = logging.getLogger(__name__)


def load_model_artifact(model_version_id: int, artifact_path: Path):

    cached = model_cache.get_model_artifact(model_version_id)

    if cached is not None:
        logger.info(f"Artifact cache Hit. model_version : %s",model_version_id)
        return cached

    logger.info("Artifact cache Miss. model_version : %s",model_version_id)

    artifact = _load_artifact(artifact_path)

    if artifact is None:
        raise ModelArtifactNotFound(str(artifact_path))

    # pytorch는 모델까지 미리 복원해서 캐싱
    if artifact.get("framework") == "PYTORCH":
        artifact["model"] = restore_model(artifact)

    model_cache.set_model_artifact(
        model_version_id,
        artifact,
    )

    return artifact


def _load_artifact(artifact_path: Path):

    suffix = artifact_path.suffix.lower()

    if suffix == ".pt":
        return torch.load(
            artifact_path,
            map_location="cuda",
        )

    if suffix == ".joblib":
        return joblib.load(
            artifact_path
        )

    raise ModelArtifactNotFound(
        f"Unsupported artifact format: "
        f"{artifact_path}"
    )
