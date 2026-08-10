from dataclasses import dataclass
from typing import Any

from app.domain.model.enums import ModelTaskType
from app.training.consts import DEFAULT_CLASSIFICATION_SELECTION_METRIC, DEFAULT_REGRESSION_SELECTION_METRIC
from app.training.schema import Recommendation


@dataclass
class RecommendationCandidate:
    algorithm: str
    model_version_id: int
    metrics: dict[str, Any]

def get_recommendation(candidates: list[RecommendationCandidate],
                       task_type: ModelTaskType) -> Recommendation | None:

    if not candidates:
        return None

    criterion_metric = (
        DEFAULT_CLASSIFICATION_SELECTION_METRIC
        if task_type == ModelTaskType.CLASSIFICATION
        else DEFAULT_REGRESSION_SELECTION_METRIC
    )

    best_candidate = max(candidates,
                         key=lambda candidate: candidate.metrics.get(criterion_metric, float("-inf")))

    return Recommendation(
        model_version_id=best_candidate.model_version_id,
        algorithm=best_candidate.algorithm,
        criterion_metric=criterion_metric,
        metric_score=best_candidate.metrics.get(
            criterion_metric,
            float("-inf"),
        ),
    )