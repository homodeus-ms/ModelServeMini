from starlette import status

from app.core.exceptions import AppException


class NotValidTaskType(AppException):

    def __init__(self, training_job_id: int, current_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task Type is not valid",
            training_job_id=training_job_id,
            current_status=current_status
        )