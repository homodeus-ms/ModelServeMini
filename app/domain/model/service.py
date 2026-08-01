from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.member.exceptions import MemberNotFound
from app.domain.member import repository as member_repository
from app.domain.model import repository
from app.domain.model.exceptions import ModelAlreadyExists, ModelNotFound
from app.domain.model.model import Model
from app.domain.model.schema import CreateModelRequest, UpdateModelRequest


def get_model(db: Session, model_id: int) -> Model:
    return _get_model_or_throw(db, model_id)


def get_models(db: Session, created_by: int | None = None) -> list[Model]:
    if created_by is not None:
        return repository.find_all_by_created_by(db, created_by)

    return repository.find_all(db)


def create_model(db: Session, request: CreateModelRequest) -> Model:
    _validate_member(db, request.created_by)
    _validate_duplicate_name(db, request.created_by, request.name)

    model = Model(
        created_by=request.created_by,
        name=request.name,
        description=request.description,
        task_type=request.task_type.value
    )

    try:
        repository.save(db, model)

        db.commit()
        db.refresh(model)

        return model

    except IntegrityError:
        db.rollback()
        raise ModelAlreadyExists(request.created_by, request.name)


def update_model(db: Session, model_id: int, request: UpdateModelRequest) -> Model:
    model = _get_model_or_throw(db, model_id)
    update_data = request.model_dump(exclude_unset=True)

    new_name = update_data.get("name")

    if new_name is not None:
        _validate_duplicate_name(db, model.created_by, new_name, model.id)

    if "name" in update_data:
        model.name = update_data["name"]

    if "description" in update_data:
        model.description = update_data["description"]

    if "task_type" in update_data:
        model.task_type = update_data["task_type"].value

    try:
        db.commit()
        db.refresh(model)

        return model

    except IntegrityError:
        db.rollback()
        raise ModelAlreadyExists(model.created_by, new_name or model.name)


def delete_model(db: Session, model_id: int) -> None:
    model = _get_model_or_throw(db, model_id)

    repository.delete(db, model)
    db.commit()

def _get_model_or_throw(db: Session, model_id: int) -> Model:
    model = repository.find_by_id(db, model_id)

    if model is None:
        raise ModelNotFound(model_id)

    return model


def _validate_member(db: Session, member_id: int) -> None:
    member = member_repository.find_by_id(db, member_id)

    if member is None:
        raise MemberNotFound(member_id)


def _validate_duplicate_name(db: Session, created_by: int, name: str, current_model_id: int | None = None) -> None:
    existing_model = repository.find_by_created_by_and_name(db, created_by, name)

    if existing_model is None:
        return

    if current_model_id is not None and existing_model.id == current_model_id:
        return

    raise ModelAlreadyExists(created_by, name)
