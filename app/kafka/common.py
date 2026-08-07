CPU_TOPIC = "training-jobs-cpu"
GPU_TOPIC = "training-jobs-gpu"

GPU_ALGORITHMS = {
    "XGBOOST_CLASSIFIER_GPU",
    "XGBOOST_REGRESSOR_GPU",
}

def get_training_topic(algorithm: str) -> str:
    if algorithm in GPU_ALGORITHMS:
        return GPU_TOPIC

    return CPU_TOPIC

