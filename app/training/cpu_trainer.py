import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.domain.dataset_version.model import DatasetVersion
from app.domain.training_job.enums import TrainingAlgorithm
from app.domain.training_job.model import TrainingJob
from app.training.artifact_storage import save_artifact
from app.training.consts import TASK_TYPE_BY_ALGORITHM
from app.training.exceptions import NotValidTaskType
from app.training.result import TrainingResult
from app.training.utils import resolve_dataset_path
from app.training_pipeline.cpu_validation import validate_cpu_features
from app.training_pipeline.estimator_factory import create_estimator
from app.training_pipeline.importance import calculate_feature_importance
from app.training_pipeline.metrics import calculate_metrics
from app.training_pipeline.pipeline_factory import create_training_pipeline
from app.training_pipeline.schema_builder import create_input_schema
from app.training_pipeline.validation import validate_dataframe, validate_feature_columns


def train(training_job: TrainingJob, dataset_ver: DatasetVersion) -> TrainingResult:
    # 입력 데이터 -> dataframe
    dataset_path = resolve_dataset_path(dataset_ver.storage_uri)
    dataframe = pd.read_csv(dataset_path)
    validate_dataframe(dataframe, training_job.target_column)

    # 입력 데이터의 칼럼명들 -> feature_columns
    feature_columns = training_job.training_config.get("feature_columns")
    validate_feature_columns(dataframe, feature_columns, training_job.target_column)

    # dataframe[column] : dataframe으로부터 해당 칼럼들에 해당하는 row추출 -> features
    features = dataframe[feature_columns].copy()
    target = dataframe[training_job.target_column]
    validate_cpu_features(features)

    algorithm = TrainingAlgorithm(training_job.algorithm)

    # Classifier 타겟 인코딩 (XGBOOST_CLASSIFIER_GPU)
    target_encoder = None
    if algorithm == TrainingAlgorithm.XGBOOST_CLASSIFIER_GPU:
        target_encoder = LabelEncoder()
        target = target_encoder.fit_transform(target)

    # train - test 비율 | random seed 값
    test_size = training_job.training_config.get("test_size", 0.2)
    random_state = training_job.training_config.get("random_state", 42)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=random_state,
    )

    estimator = create_estimator(algorithm, training_job.training_config)

    # sklearn Pipeline - 파이프라인(각 칼럼 전처리기 -> 추정기) 생성
    pipeline = create_training_pipeline(features, estimator)

    # 학습 | 테스트
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    # metrics, feature_importance
    metrics = calculate_metrics(algorithm, y_test, predictions)

    # feature importance
    task_type = TASK_TYPE_BY_ALGORITHM.get(algorithm)
    if task_type is None:
        raise NotValidTaskType("Algorithm not supported")
    feature_importances = calculate_feature_importance(pipeline, x_test, y_test, task_type)

    # artifact 저장
    artifact = {"pipeline": pipeline, "target_encoder": target_encoder}
    artifact_uri, artifact_size, artifact_checksum = save_artifact(artifact, training_job.model_id)

    return TrainingResult(
        artifact_uri=artifact_uri,
        artifact_size=artifact_size,
        artifact_checksum=artifact_checksum,
        metrics=metrics,
        input_schema=create_input_schema(features),
        feature_columns=list(features.columns),
        feature_importances=feature_importances,
    )