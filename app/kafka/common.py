from app.training.algorithm_registry import GPU_ALGORITHMS

CPU_TOPIC = "training-jobs-cpu"
GPU_TOPIC = "training-jobs-gpu"

CPU_TOPIC_PARTITION_COUNT = 3
GPU_TOPIC_PARTITION_COUNT = 1

def get_training_topic(algorithm: str) -> str:
    if algorithm in GPU_ALGORITHMS:
        return GPU_TOPIC

    return CPU_TOPIC

