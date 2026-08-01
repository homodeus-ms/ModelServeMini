import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.dataset import repository as dataset_repository
from app.domain.dataset.exceptions import DatasetNotFound
from app.domain.dataset_version import repository
from app.domain.dataset_version.csv_validator import validate_csv
from app.domain.dataset_version.enums import DatasetVersionStatus
from app.domain.dataset_version.exceptions import (
    DatasetFileRequired,
    DatasetFileSaveFailed,
    DatasetVersionNotFound,
    UnsupportedDatasetFile, DatasetVersionNotValidatable, DatasetFileNotFound,
)
from app.domain.dataset_version.model import DatasetVersion
from app.domain.member import repository as member_repository
from app.domain.member.exceptions import MemberNotFound


def get_dataset_version(db: Session, dataset_version_id: int) -> DatasetVersion:
    return _get_dataset_version_or_throw(db, dataset_version_id)


def get_dataset_versions(db: Session, dataset_id: int) -> list[DatasetVersion]:
    dataset = dataset_repository.find_by_id(db, dataset_id)

    if dataset is None:
        raise DatasetNotFound(dataset_id)

    return repository.find_all_by_dataset_id(db, dataset_id)


def create_dataset_version(db: Session, dataset_id: int, created_by: int, file: UploadFile) -> DatasetVersion:
    dataset = dataset_repository.find_by_id(db, dataset_id)

    if dataset is None:
        raise DatasetNotFound(dataset_id)

    member = member_repository.find_by_id(db, created_by)

    if member is None:
        raise MemberNotFound(created_by)

    _validate_csv_file(file)

    original_filename = file.filename
    storage_path = _create_storage_path(dataset_id, original_filename)
    file_size, checksum = _save_file(file, storage_path)
    version = repository.find_next_version(db, dataset_id)

    dataset_version = DatasetVersion(
        dataset_id=dataset_id,
        created_by=created_by,
        version=version,
        original_filename=original_filename,
        storage_uri=str(storage_path),
        file_size=file_size,
        content_type=file.content_type or "text/csv",
        checksum=checksum,
        status=DatasetVersionStatus.UPLOADED.value
    )

    try:
        repository.save(db, dataset_version)
        db.commit()
        db.refresh(dataset_version)

    except Exception:
        db.rollback()
        storage_path.unlink(missing_ok=True)
        raise

    return dataset_version

def validate_dataset_version(db: Session, dataset_version_id: int) -> DatasetVersion:
    dataset_version = _get_dataset_version_or_throw(db, dataset_version_id)

    valid_statuses = {
        DatasetVersionStatus.UPLOADED.value,
        DatasetVersionStatus.INVALID.value,
        DatasetVersionStatus.FAILED.value
    }

    if dataset_version.status not in valid_statuses:
        raise DatasetVersionNotValidatable(
            dataset_version.id,
            dataset_version.status
        )

    storage_path = Path(dataset_version.storage_uri)

    if not storage_path.exists():
        raise DatasetFileNotFound(dataset_version.storage_uri)

    dataset_version.status = DatasetVersionStatus.VALIDATING.value
    db.commit()

    try:
        result = validate_csv(storage_path)

        dataset_version.row_count = result["row_count"]
        dataset_version.column_count = result["column_count"]
        dataset_version.schema_definition = result["schema_definition"]
        dataset_version.validation_report = result["validation_report"]

        if result["valid"]:
            dataset_version.status = DatasetVersionStatus.READY.value
        else:
            dataset_version.status = DatasetVersionStatus.INVALID.value

        db.commit()
        db.refresh(dataset_version)

        return dataset_version

    except Exception as exc:
        db.rollback()

        dataset_version = _get_dataset_version_or_throw(
            db,
            dataset_version_id
        )

        dataset_version.status = DatasetVersionStatus.FAILED.value
        dataset_version.validation_report = {
            "valid": False,
            "errors": [str(exc)],
            "warnings": []
        }

        db.commit()
        raise


def delete_dataset_version(db: Session, dataset_version_id: int) -> None:
    dataset_version = _get_dataset_version_or_throw(db, dataset_version_id)
    storage_path = Path(dataset_version.storage_uri)

    repository.delete(db, dataset_version)
    db.commit()

    storage_path.unlink(missing_ok=True)


def _get_dataset_version_or_throw(db: Session, dataset_version_id: int) -> DatasetVersion:
    dataset_version = repository.find_by_id(db, dataset_version_id)

    if dataset_version is None:
        raise DatasetVersionNotFound(dataset_version_id)

    return dataset_version


def _validate_csv_file(file: UploadFile) -> None:
    if file.filename is None or file.filename.strip() == "":
        raise DatasetFileRequired()

    if Path(file.filename).suffix.lower() != ".csv":
        raise UnsupportedDatasetFile(file.filename)


def _create_storage_path(dataset_id: int, original_filename: str) -> Path:
    extension = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4().hex}{extension}"
    directory = Path(settings.dataset_storage_path) / str(dataset_id)

    directory.mkdir(parents=True, exist_ok=True)

    return directory / stored_filename


def _save_file(file: UploadFile, storage_path: Path) -> tuple[int, str]:
    checksum = hashlib.sha256()
    file_size = 0

    try:
        with storage_path.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                output.write(chunk)
                checksum.update(chunk)
                file_size += len(chunk)

    except OSError:
        storage_path.unlink(missing_ok=True)
        raise DatasetFileSaveFailed(file.filename or "unknown")

    return file_size, checksum.hexdigest()