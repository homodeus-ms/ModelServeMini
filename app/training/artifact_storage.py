import hashlib
import os
from pathlib import Path
from uuid import uuid4

import joblib
import torch

from app.core.config import settings


# artifact 저장, 현재는 Local drive에 -> TODO: 이후에 외부 저장소로 변경
def save_artifact(artifact, model_id: int) -> tuple[str, int, str]:

    relative_path = Path("models") / str(model_id) / f"{uuid4().hex}.joblib"

    artifact_path = Path(settings.model_storage_path) / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(artifact, artifact_path)
    artifact_size = artifact_path.stat().st_size
    artifact_checksum = _calculate_checksum(artifact_path)

    return (
        str(relative_path),
        artifact_size,
        artifact_checksum,
    )

def save_pytorch_artifact(artifact: dict, model_id: int) -> tuple[str, int, str]:

    relative_path = Path("models") / str(model_id) / f"{uuid4().hex}.pt"
    artifact_path = Path(settings.model_storage_path) / relative_path

    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    torch.save(artifact, artifact_path)

    artifact_size = artifact_path.stat().st_size
    artifact_checksum = _calculate_checksum(artifact_path)

    return str(relative_path), artifact_size, artifact_checksum,



def _calculate_checksum(path: Path) -> str:
    checksum = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            checksum.update(chunk)

    return checksum.hexdigest()