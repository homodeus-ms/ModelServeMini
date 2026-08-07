from typing import Any

from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor,
)
from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression,
)
from xgboost import XGBClassifier, XGBRegressor

from app.domain.training_job.enums import TrainingAlgorithm


def create_estimator(algorithm: TrainingAlgorithm, config: dict[str, Any]):

    match algorithm:

        ## Classifier
        case TrainingAlgorithm.LOGISTIC_REGRESSION:
            return LogisticRegression(
                max_iter=1000,
                random_state=42,
            )

        case TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER:
            return RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=4,
            )

        case TrainingAlgorithm.GRADIENT_BOOSTING_CLASSIFIER:
            return GradientBoostingClassifier(
                n_estimators=100,
                random_state=42,
            )
        case TrainingAlgorithm.XGBOOST_CLASSIFIER_GPU:
            return XGBClassifier(
                n_estimators=300,
                max_depth=8,
                learning_rate=0.1,
                tree_method="hist",
                device="cuda",
                random_state=42,
                eval_metric="logloss",
            )

        ## Regressor
        case TrainingAlgorithm.LINEAR_REGRESSION:
            return LinearRegression()

        case TrainingAlgorithm.RANDOM_FOREST_REGRESSOR:
            return RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                n_jobs=4,
            )

        case TrainingAlgorithm.GRADIENT_BOOSTING_REGRESSOR:
            return GradientBoostingRegressor(
                n_estimators=100,
                random_state=42,
            )

        case TrainingAlgorithm.XGBOOST_REGRESSOR_GPU:
            return XGBRegressor(
                n_estimators=300,
                max_depth=8,
                learning_rate=0.1,
                tree_method="hist",
                device="cuda",
                random_state=42,
                eval_metric="rmse",
            )

        case _:
            raise ValueError(f"Unknown training algorithm {algorithm}")