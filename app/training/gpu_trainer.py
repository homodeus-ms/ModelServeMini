import logging

import cudf
import cuml
import cupy as cp
from cuml.preprocessing import LabelEncoder
from cuml.model_selection import train_test_split

from app.training.artifact_storage import save_artifact
from app.training.algorithm_registry import TASK_TYPE_BY_ALGORITHM
from app.training.exceptions import NotValidTaskType
from app.training_pipeline.gpu_importance import gpu_calculate_feature_importance
from app.training_pipeline.gpu_validation import validate_gpu_features
from app.training_pipeline.metrics import calculate_metrics
from app.training_pipeline.schema_builder import create_input_schema

cuml.set_global_output_type("cupy")

from app.domain.dataset_version.model import DatasetVersion
from app.domain.training_job.enums import TrainingAlgorithm
from app.domain.training_job.model import TrainingJob
from app.training.result import TrainingResult
from app.training.utils import resolve_dataset_path
from app.training_pipeline.estimator_factory import create_estimator
from app.training_pipeline.gpu_pipeline_factory import create_gpu_training_pipeline
from app.training_pipeline.validation import validate_dataframe, validate_feature_columns

logger = logging.getLogger(__name__)

def train(training_job: TrainingJob, dataset_ver: DatasetVersion) -> TrainingResult:

    dataset_path = resolve_dataset_path(dataset_ver.storage_uri)

    # Vram에 읽기
    dataframe = cudf.read_csv(dataset_path)

    # TEMP : 벤치마크 테스트용
    dataframe = cudf.concat([dataframe] * 3000, ignore_index=True)
    logger.info("benchmark dataframe rows=%s",len(dataframe))

    validate_dataframe(dataframe, training_job.target_column)

    # 입력 데이터의 칼럼명들 -> feature_columns
    feature_columns = training_job.training_config.get("feature_columns")
    validate_feature_columns(dataframe, feature_columns, training_job.target_column)

    # dataframe[column] : dataframe으로부터 해당 칼럼들에 해당하는 row추출 -> features
    features = dataframe[feature_columns].copy()
    target = dataframe[training_job.target_column]
    validate_gpu_features(features)

    algorithm = TrainingAlgorithm(training_job.algorithm)

    target_encoder = None
    if algorithm == TrainingAlgorithm.XGBOOST_CLASSIFIER_GPU:
        target_encoder = LabelEncoder()
        target = target_encoder.fit_transform(target)

    test_size = training_job.training_config.get("test_size", 0.2)
    random_state = training_job.training_config.get("random_state", 42)

    # CPU쪽에서 SimpleImputer 하는 부분 GPU쪽에선 fillna를 사용해서 이렇게
    categorical_columns = list(
        features.select_dtypes(include=["str", "category"]).columns
    )
    for column in categorical_columns:
        most_frequent_value = features[column].mode().iloc[0]
        features[column] = features[column].fillna(most_frequent_value)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=random_state,
    )

    estimator = create_estimator(algorithm, training_job.training_config)

    pipeline = create_gpu_training_pipeline(features, estimator)

    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    metrics = calculate_metrics(algorithm, cp.asnumpy(y_test), cp.asnumpy(predictions))

    task_type = TASK_TYPE_BY_ALGORITHM.get(algorithm)
    if task_type is None:
        raise NotValidTaskType("Algorithm not supported")
    feature_importances = gpu_calculate_feature_importance(pipeline, x_test, y_test, metrics)

    # artifact 저장 (GPU 파이프라인 그대로 저장함)
    artifact = {"pipeline": pipeline, "target_encoder": target_encoder, "task_type": task_type.value}
    artifact_uri, artifact_size, artifact_checksum = save_artifact(artifact, training_job.model_id)

    result = TrainingResult(
        artifact_uri=artifact_uri,
        artifact_size=artifact_size,
        artifact_checksum=artifact_checksum,
        metrics=metrics,
        input_schema=create_input_schema(features),
        feature_columns=list(features.columns),
        feature_importances=feature_importances,
    )

    return result