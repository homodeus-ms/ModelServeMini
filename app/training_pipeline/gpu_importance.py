import logging

from cuml.pipeline import Pipeline

from app.domain.model.enums import ModelTaskType

logger = logging.getLogger(__name__)

def gpu_calculate_feature_importance(pipeline: Pipeline, x_test, y_test,
                                 task_type: ModelTaskType) -> list[dict[str, float | str]]:

    estimator = pipeline.named_steps["estimator"]
    preprocessor = pipeline.named_steps["preprocessor"]
    categorical_pipeline = preprocessor.named_transformers_["categorical"]
    encoder = categorical_pipeline.named_steps["encoder"]

    numeric_columns = list(x_test.select_dtypes(include="number").columns)
    categorical_columns = list(x_test.select_dtypes(include=["str", "category"]).columns)
    raw_importances = estimator.feature_importances_

    index = 0
    result: dict[str, float] = {}

    # raw_importances 는 1차원 배열
    # numeric이 먼저옴
    for column in numeric_columns:
        result[column] = float(raw_importances[index])
        index += 1

    # encoder.categories_ : oneHotEncoding 전 어떤 카테고리 값들이 존재했는지
    # 예) gender -> categorical_columns : gender , encoder.categories : array(['F', 'M'])
    for column, categories in zip(categorical_columns, encoder.categories_):
        category_count = len(categories)
        result[column] = float(sum(raw_importances[index:index + category_count]))
        index += category_count

    return sorted(
        [
            {
                "feature": feature,
                "importance": importance,
            }
            for feature, importance in result.items()
        ],
        key=lambda item:item["importance"],
        reverse=True,
    )



def _calculate_feature_importance(raw_importances,
                                  categorical_columns,
                                  numeric_columns,
                                  encoder_categories) -> dict[str, float]:
    index = 0
    result: dict[str, float] = {}

    for column in numeric_columns:
        result[column] = float(raw_importances[index])
        index += 1

    for column, categories in zip(categorical_columns, encoder_categories):
        category_count = len(categories)
        result[column] = float(sum(raw_importances[index:index + category_count]))
        index += category_count

    return result