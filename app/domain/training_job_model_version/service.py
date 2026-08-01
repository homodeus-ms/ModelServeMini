from sqlalchemy.orm import Session

from app.domain.training_job_model_version import repository
from app.domain.training_job_model_version.enums import ModelVersionRelationType
from app.domain.training_job_model_version.model import TrainingJobModelVersion


# 여기선 commit 하지 않음
def create_base_relation(db: Session, training_job_id: int, model_version_id: int) -> TrainingJobModelVersion:
    relation = TrainingJobModelVersion(
        training_job_id=training_job_id,
        relation_type=ModelVersionRelationType.BASE.value,
        model_version_id=model_version_id
    )
    return repository.save(db, relation)


def create_result_relation(db: Session, training_job_id: int, model_version_id: int) -> TrainingJobModelVersion:
    relation = TrainingJobModelVersion(
        training_job_id=training_job_id,
        relation_type=ModelVersionRelationType.RESULT.value,
        model_version_id=model_version_id
    )
    return repository.save(db, relation)