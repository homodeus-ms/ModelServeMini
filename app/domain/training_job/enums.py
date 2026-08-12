from enum import Enum, StrEnum

class TrainingJobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


####################################################
# training_job.enums - ALGORITHM_REGISTRY 일관성 유지!
####################################################

class TrainingAlgorithm(str, Enum):
    # Classifier
    LOGISTIC_REGRESSION = "LOGISTIC_REGRESSION"
    RANDOM_FOREST_CLASSIFIER = "RANDOM_FOREST_CLASSIFIER"
    GRADIENT_BOOSTING_CLASSIFIER = "GRADIENT_BOOSTING_CLASSIFIER"
    XGBOOST_CLASSIFIER_GPU = "XGBOOST_CLASSIFIER_GPU"
    PYTORCH_MLP_CLASSIFIER = "PYTORCH_MLP_CLASSIFIER"

    # Regressor
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    RANDOM_FOREST_REGRESSOR = "RANDOM_FOREST_REGRESSOR"
    GRADIENT_BOOSTING_REGRESSOR = "GRADIENT_BOOSTING_REGRESSOR"
    XGBOOST_REGRESSOR_GPU = "XGBOOST_REGRESSOR_GPU",
    PYTORCH_MLP_REGRESSOR = "PYTORCH_MLP_REGRESSOR"


class ExecutionDevice(StrEnum):
    CPU = "CPU"
    GPU = "GPU"

# DEVICE_BY_ALGORITHM = {
#     TrainingAlgorithm.LOGISTIC_REGRESSION:
#         ExecutionDevice.CPU,
#
#     TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER:
#         ExecutionDevice.CPU,
#
#     TrainingAlgorithm.GRADIENT_BOOSTING_CLASSIFIER:
#         ExecutionDevice.CPU,
#
#     TrainingAlgorithm.XGBOOST_CLASSIFIER_GPU:
#         ExecutionDevice.GPU,
#
#     TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER:
#         ExecutionDevice.GPU,
#
#     TrainingAlgorithm.LINEAR_REGRESSION:
#         ExecutionDevice.CPU,
#
#     TrainingAlgorithm.RANDOM_FOREST_REGRESSOR:
#         ExecutionDevice.CPU,
#
#     TrainingAlgorithm.GRADIENT_BOOSTING_REGRESSOR:
#         ExecutionDevice.CPU,
#
#     TrainingAlgorithm.XGBOOST_REGRESSOR_GPU:
#         ExecutionDevice.GPU,
#
#     TrainingAlgorithm.PYTORCH_MLP_REGRESSOR:
#         ExecutionDevice.GPU,
# }
