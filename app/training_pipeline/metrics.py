from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score, precision_score, recall_score, f1_score,
)

from app.domain.model.enums import ModelTaskType
from app.domain.training_job.enums import TrainingAlgorithm
from app.training.algorithm_registry import ALGORITHMS_BY_TASK_TYPE

CLASSIFICATION_ALGORITHMS = ALGORITHMS_BY_TASK_TYPE.get(ModelTaskType.CLASSIFICATION)

def calculate_metrics(algorithm: TrainingAlgorithm, y_test, predictions) -> dict[str, float]:

    if algorithm in CLASSIFICATION_ALGORITHMS:

        return {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(precision_score(y_test, predictions, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, predictions, average="weighted", zero_division=0)),
            "f1_score": float(f1_score(y_test, predictions, average="weighted", zero_division=0)),
        }

    mse = mean_squared_error(y_test, predictions)

    return {
        "mae": float(mean_absolute_error(y_test, predictions)),
        "mse": float(mse),
        "rmse": float(mse ** 0.5),
        "r2": float(r2_score(y_test, predictions)),
    }