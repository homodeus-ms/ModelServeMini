import os

from pathlib import Path


def resolve_dataset_path(storage_uri: str) -> Path:
    base_path = Path(
        os.getenv("DATASET_STORAGE_PATH", "storage/datasets")
    )

    normalized_path = Path(
        storage_uri.replace("\\", "/")
    )

    # 기존 DB 값이 storage/datasets/... 형식이므로 앞부분 제거
    if normalized_path.parts[:2] == ("storage", "datasets"):
        normalized_path = Path(*normalized_path.parts[2:])

    return base_path / normalized_path