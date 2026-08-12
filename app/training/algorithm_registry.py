from dataclasses import dataclass

from app.domain.model.enums import ModelTaskType
from app.domain.training_job.enums import ExecutionDevice, TrainingAlgorithm


####################################################
# training_job.enums - ALGORITHM_REGISTRY 일관성 유지!
####################################################


@dataclass(frozen=True)
class AlgorithmSpec:
    task_type: ModelTaskType
    device: ExecutionDevice


ALGORITHM_REGISTRY: dict[TrainingAlgorithm, AlgorithmSpec] = {

    # Classifier
    TrainingAlgorithm.LOGISTIC_REGRESSION:
        AlgorithmSpec(task_type=ModelTaskType.CLASSIFICATION, device=ExecutionDevice.CPU),

    TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER:
        AlgorithmSpec(task_type=ModelTaskType.CLASSIFICATION, device=ExecutionDevice.CPU),

    TrainingAlgorithm.GRADIENT_BOOSTING_CLASSIFIER:
        AlgorithmSpec(task_type=ModelTaskType.CLASSIFICATION, device=ExecutionDevice.CPU),

    TrainingAlgorithm.XGBOOST_CLASSIFIER_GPU:
        AlgorithmSpec(task_type=ModelTaskType.CLASSIFICATION, device=ExecutionDevice.GPU),

    TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER:
        AlgorithmSpec(task_type=ModelTaskType.CLASSIFICATION, device=ExecutionDevice.GPU),

    #Regressor
    TrainingAlgorithm.LINEAR_REGRESSION:
        AlgorithmSpec(task_type=ModelTaskType.REGRESSION, device=ExecutionDevice.CPU),

    TrainingAlgorithm.RANDOM_FOREST_REGRESSOR:
        AlgorithmSpec(task_type=ModelTaskType.REGRESSION, device=ExecutionDevice.CPU),

    TrainingAlgorithm.GRADIENT_BOOSTING_REGRESSOR:
        AlgorithmSpec(task_type=ModelTaskType.REGRESSION, device=ExecutionDevice.CPU),

    TrainingAlgorithm.XGBOOST_REGRESSOR_GPU:
        AlgorithmSpec(task_type=ModelTaskType.REGRESSION, device=ExecutionDevice.GPU),

    TrainingAlgorithm.PYTORCH_MLP_REGRESSOR:
        AlgorithmSpec(task_type=ModelTaskType.REGRESSION, device=ExecutionDevice.GPU),
}


ALGORITHMS_BY_TASK_TYPE = {
    task_type: [algorithm
                for algorithm, spec in ALGORITHM_REGISTRY.items()
                if spec.task_type == task_type]
    for task_type in ModelTaskType
}

TASK_TYPE_BY_ALGORITHM = {
    algorithm: spec.task_type
    for algorithm, spec in ALGORITHM_REGISTRY.items()
}

DEVICE_BY_ALGORITHM = {
    algorithm: spec.device
    for algorithm, spec in ALGORITHM_REGISTRY.items()
}

GPU_ALGORITHMS = {
    algorithm
    for algorithm, spec in ALGORITHM_REGISTRY.items()
    if spec.device == ExecutionDevice.GPU
}

CPU_ALGORITHMS = {
    algorithm
    for algorithm, spec in ALGORITHM_REGISTRY.items()
    if spec.device == ExecutionDevice.CPU
}


