from app.domain.model.enums import ModelTaskType
from app.domain.training_job.enums import TrainingAlgorithm

ALGORITHMS_BY_TASK_TYPE: dict[ModelTaskType, list[TrainingAlgorithm]] = {
    ModelTaskType.CLASSIFICATION: [
        TrainingAlgorithm.LOGISTIC_REGRESSION,
        TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER,
    ],
    ModelTaskType.REGRESSION: [
        TrainingAlgorithm.LINEAR_REGRESSION,
        TrainingAlgorithm.RANDOM_FOREST_REGRESSOR,
    ],
}

TASK_TYPE_BY_ALGORITHM: dict[TrainingAlgorithm, ModelTaskType] = {
    TrainingAlgorithm.LOGISTIC_REGRESSION: ModelTaskType.CLASSIFICATION,
    TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER: ModelTaskType.CLASSIFICATION,
    TrainingAlgorithm.LINEAR_REGRESSION: ModelTaskType.REGRESSION,
    TrainingAlgorithm.RANDOM_FOREST_REGRESSOR: ModelTaskType.REGRESSION,
}

DEFAULT_CLASSIFICATION_SELECTION_METRIC = "f1_score"
DEFAULT_REGRESSION_SELECTION_METRIC = "r2"
