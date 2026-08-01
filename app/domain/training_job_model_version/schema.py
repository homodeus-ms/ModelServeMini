from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.training_job_model_version.enums import ModelVersionRelationType


class TrainingJobModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    training_job_id: int
    relation_type: ModelVersionRelationType
    model_version_id: int
    created_at: datetime