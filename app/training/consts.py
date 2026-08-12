from app.domain.model.enums import ModelTaskType
from app.domain.training_job.enums import TrainingAlgorithm

#CPU_ALGORITHM_COUNT = 3
#GPU_ALGORITHM_COUNT = 2

# ALGORITHMS_BY_TASK_TYPE: dict[ModelTaskType, list[TrainingAlgorithm]] = {
#     ModelTaskType.CLASSIFICATION: [
#         TrainingAlgorithm.LOGISTIC_REGRESSION,
#         TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER,
#         TrainingAlgorithm.GRADIENT_BOOSTING_CLASSIFIER,
#         TrainingAlgorithm.XGBOOST_CLASSIFIER_GPU,
#         TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER
#     ],
#     ModelTaskType.REGRESSION: [
#         TrainingAlgorithm.LINEAR_REGRESSION,
#         TrainingAlgorithm.RANDOM_FOREST_REGRESSOR,
#         TrainingAlgorithm.GRADIENT_BOOSTING_REGRESSOR,
#         TrainingAlgorithm.XGBOOST_REGRESSOR_GPU,
#         TrainingAlgorithm.PYTORCH_MLP_REGRESSOR
#     ],
# }

# CURRENT_ALGORITHM_COUNT = 5

# TASK_TYPE_BY_ALGORITHM: dict[TrainingAlgorithm, ModelTaskType] = {
#
#     TrainingAlgorithm.LOGISTIC_REGRESSION: ModelTaskType.CLASSIFICATION,
#     TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER: ModelTaskType.CLASSIFICATION,
#     TrainingAlgorithm.GRADIENT_BOOSTING_CLASSIFIER: ModelTaskType.CLASSIFICATION,
#     TrainingAlgorithm.XGBOOST_CLASSIFIER_GPU: ModelTaskType.CLASSIFICATION,
#     TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER: ModelTaskType.CLASSIFICATION,
#
#     TrainingAlgorithm.LINEAR_REGRESSION: ModelTaskType.REGRESSION,
#     TrainingAlgorithm.RANDOM_FOREST_REGRESSOR: ModelTaskType.REGRESSION,
#     TrainingAlgorithm.GRADIENT_BOOSTING_REGRESSOR: ModelTaskType.REGRESSION,
#     TrainingAlgorithm.XGBOOST_REGRESSOR_GPU: ModelTaskType.REGRESSION,
#     TrainingAlgorithm.PYTORCH_MLP_REGRESSOR: ModelTaskType.REGRESSION
# }

DEFAULT_CLASSIFICATION_SELECTION_METRIC = "f1_score"
DEFAULT_REGRESSION_SELECTION_METRIC = "r2"
