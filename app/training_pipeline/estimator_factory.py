from typing import Any

from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression,
)

from app.domain.training_job.enums import TrainingAlgorithm


def create_estimator(algorithm: TrainingAlgorithm, config: dict[str, Any]):

    if algorithm == TrainingAlgorithm.LOGISTIC_REGRESSION:
        return LogisticRegression(
            max_iter=config.get("max_iter", 1000),
            random_state=config.get("random_state", 42),
        )

    if algorithm == TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER:
        return RandomForestClassifier(
            n_estimators=config.get("n_estimators", 100),
            random_state=config.get("random_state", 42),
        )

    if algorithm == TrainingAlgorithm.LINEAR_REGRESSION:
        return LinearRegression()

    if algorithm == TrainingAlgorithm.RANDOM_FOREST_REGRESSOR:
        return RandomForestRegressor(
            n_estimators=config.get("n_estimators", 100),
            random_state=config.get("random_state", 42),
        )

    raise ValueError(f"Unsupported algorithm: {algorithm}")