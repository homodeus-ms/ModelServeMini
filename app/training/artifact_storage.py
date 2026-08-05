import hashlib
import os
from pathlib import Path
from uuid import uuid4

import joblib


# artifact 저장, 현재는 Local drive에 -> TODO: 이후에 외부 저장소로 변경
def save_artifact(pipeline, model_id: int) -> tuple[str, int, str]:
    base_path = os.getenv("MODEL_STORAGE_PATH", "storage/models")
    directory = Path(base_path) / str(model_id)
    directory.mkdir(parents=True, exist_ok=True)

    artifact_path = directory / f"{uuid4().hex}.joblib"
    joblib.dump(pipeline, artifact_path)

    artifact_size = artifact_path.stat().st_size
    artifact_checksum = _calculate_checksum(artifact_path)

    return str(artifact_path), artifact_size, artifact_checksum


def _calculate_checksum(path: Path) -> str:
    checksum = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            checksum.update(chunk)

    return checksum.hexdigest()