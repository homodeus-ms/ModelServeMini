from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.model_selection import train_test_split

from app.domain.dataset_version.model import DatasetVersion
from app.domain.training_job.enums import TrainingAlgorithm
from app.domain.training_job.model import TrainingJob
from app.training.artifact_storage import save_artifact
from app.training.result import TrainingResult

# <현재 trainer의 지원 범위>
# CSV 파일
# 숫자형 입력 컬럼
# 결측치 없는 데이터
# 분류 또는 회귀
# 간단한 train/test 분리
# accuracy 또는 RMSE
# .joblib 저장

# TODO:
# 문자열 카테고리 인코딩, 결측치 보정, 정규화 같은 전처리

CLASSIFICATION_ALGORITHMS = {
    TrainingAlgorithm.LOGISTIC_REGRESSION.value,
    TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER.value,
}

# 학습 파이프라인 메인 함수
def train(training_job: TrainingJob, dataset_ver: DatasetVersion) -> TrainingResult:
    dataframe = pd.read_csv(dataset_ver.storage_uri)
    _validate_dataframe(dataframe, training_job.target_column)

    x = dataframe.drop(columns=[training_job.target_column])
    y = dataframe[training_job.target_column]
    _validate_features(x)

    test_size = training_job.training_config.get("test_size", 0.2)
    random_state = training_job.training_config.get("random_state", 42)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_size, random_state=random_state)

    estimator = _create_estimator(training_job.algorithm, training_job.training_config)
    estimator.fit(x_train, y_train)

    predictions = estimator.predict(x_test)
    metrics = _calculate_metrics(training_job.algorithm, y_test, predictions)

    artifact_uri, artifact_size, artifact_checksum = save_artifact(
        estimator,
        training_job.model_id
    )

    return TrainingResult(
        artifact_uri=artifact_uri,
        artifact_size=artifact_size,
        artifact_checksum=artifact_checksum,
        metrics=metrics,
        input_schema=_create_input_schema(x)
    )


def _create_estimator(algorithm: str, config: dict[str, Any]):
    if algorithm == TrainingAlgorithm.LOGISTIC_REGRESSION.value:
        return LogisticRegression(
            max_iter=config.get("max_iter", 1000),
            random_state=config.get("random_state", 42),
        )

    if algorithm == TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER.value:
        return RandomForestClassifier(
            n_estimators=config.get("n_estimators", 100),
            random_state=config.get("random_state", 42)
        )

    if algorithm == TrainingAlgorithm.LINEAR_REGRESSION.value:
        return LinearRegression()

    if algorithm == TrainingAlgorithm.RANDOM_FOREST_REGRESSOR.value:
        return RandomForestRegressor(
            n_estimators=config.get("n_estimators", 100),
            random_state=config.get("random_state", 42)
        )

    raise ValueError(f"Unsupported algorithm: {algorithm}")

def _calculate_metrics(algorithm: str, y_test, predictions) -> dict[str, float]:
    if algorithm in CLASSIFICATION_ALGORITHMS:
        return {
            "accuracy": float(accuracy_score(y_test, predictions)),
        }

    # 일단 분류 알고리듬이 아니면 회귀문제로 간주함
    mse = mean_squared_error(y_test, predictions)

    return {
        "rmse": float(mse ** 0.5)
    }


def _validate_dataframe(dataframe: pd.DataFrame, target_column: str) -> None:
    if dataframe.empty:
        raise ValueError("Dataset is empty")

    if target_column not in dataframe.columns:
        raise ValueError(f"Target column not found: {target_column}")

    if dataframe[target_column].isnull().any():
        raise ValueError("Target column contains null values")

def _validate_features(features: pd.DataFrame) -> None:
    if features.empty:
        raise ValueError("Dataset has no feature columns")

    non_numeric_columns = list(
        features.select_dtypes(exclude="number").columns
    )

    if non_numeric_columns:
        raise ValueError(
            f"Only numeric feature columns are supported: {non_numeric_columns}"
        )

    if features.isnull().any().any():
        raise ValueError("Feature columns contain null values")

def _create_input_schema(features: pd.DataFrame) -> dict[str, Any]:
    return {
        "columns": [
            {
                "name": column,
                "dtype": str(features[column].dtype)
            }
            for column in features.columns
        ]
    }