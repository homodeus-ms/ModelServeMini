from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline

from app.domain.model.enums import ModelTaskType


def calculate_feature_importance(pipeline: Pipeline, x_test, y_test,
                                 task_type: ModelTaskType) -> list[dict[str, float | str]]:
    scoring = _get_scoring(task_type)
    result = permutation_importance(estimator=pipeline, X=x_test, y=y_test, scoring=scoring,
                                    n_repeats=10, n_jobs=-1, random_state=42)

    importances = [
        {
            "feature": str(feature),
            "importance": float(importance),
        }
        for feature, importance in zip(
            x_test.columns,
            result.importances_mean,
        )
    ]

    return sorted(importances, key=lambda item: item["importance"], reverse=True)


def _get_scoring(task_type: ModelTaskType) -> str:
    return "f1_weighted" if task_type == ModelTaskType.CLASSIFICATION else "neg_root_mean_squared_error"