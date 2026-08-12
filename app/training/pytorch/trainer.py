import logging
import os
import time

import cudf
import torch

from torch.utils.data import DataLoader
from app.domain.dataset_version.model import DatasetVersion
from app.domain.model.enums import ModelTaskType
from app.domain.training_job.enums import TrainingAlgorithm
from app.domain.training_job.model import TrainingJob

from app.gpu_scheduler.client import (
    acquire_gpu,
    release_gpu,
    should_yield_gpu,
)
from app.gpu_scheduler.schema import GpuTaskType

from app.training.artifact_storage import save_pytorch_artifact
from app.training.algorithm_registry import TASK_TYPE_BY_ALGORITHM
from app.training.exceptions import NotValidTaskType
from app.training.pytorch.importance import calculate_feature_importance
from app.training.result import TrainingResult
from app.training.utils import resolve_dataset_path

from app.training.pytorch.artifact import create_pytorch_artifact
from app.training.pytorch.checkpoint import (
    get_checkpoint_path,
    load_checkpoint,
    save_checkpoint,
)
from app.training.pytorch.evaluation import evaluate_model
from app.training.pytorch.training_factory import (
    create_training_components,
)

from app.training_pipeline.metrics import calculate_metrics
from app.training_pipeline.schema_builder import create_input_schema


YIELD_CHECK_INTERVAL_SECONDS = 1.0
TOTAL_EPOCHS = 10
BATCH_SIZE = 64
HIDDEN_SIZE = 128
LEARNING_RATE = 0.001

logger = logging.getLogger(__name__)


def get_task_id(
    training_job_id: int,
) -> str:
    return f"training-{training_job_id}"


def train(
    training_job: TrainingJob,
    dataset_ver: DatasetVersion,
) -> TrainingResult:

    task_id = get_task_id(
        training_job.id
    )

    checkpoint_path = get_checkpoint_path(
        training_job.id
    )

    # =========================
    # Dataset
    # =========================

    dataset_path = resolve_dataset_path(
        dataset_ver.storage_uri
    )

    dataframe = cudf.read_csv(
        dataset_path
    )

    # TEMP: GPU preemption 테스트용
    dataframe = cudf.concat(
        [dataframe] * 100,
        ignore_index=True,
    )
    logger.info(
        "benchmark dataframe rows=%s",
        len(dataframe),
    )


    feature_columns = (
        training_job.training_config.get(
            "feature_columns"
        )
    )

    raw_features = dataframe[
        feature_columns
    ].copy()

    raw_feature_columns = list(
        raw_features.columns
    )

    target = dataframe[
        training_job.target_column
    ]

    # =========================
    # Algorithm / config
    # =========================

    algorithm = TrainingAlgorithm(
        training_job.algorithm
    )

    test_size = (
        training_job.training_config.get(
            "test_size",
            0.2,
        )
    )

    random_state = (
        training_job.training_config.get(
            "random_state",
            42,
        )
    )

    # =========================
    # PyTorch components
    # =========================

    components = create_training_components(
        algorithm=algorithm,
        features=raw_features,
        target=target,
        hidden_size=HIDDEN_SIZE,
        test_size=test_size,
        random_state=random_state,
    )

    model = components.model
    loss_fn = components.loss_fn

    train_dataset = components.train_dataset
    test_dataset = components.test_dataset

    input_size = components.input_size

    encoded_feature_columns = components.encoded_feature_columns
    num_classes = components.num_classes
    target_categories = components.target_categories

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    # =========================
    # Checkpoint restore
    # =========================

    start_epoch = 0
    start_batch = 0

    if os.path.exists(checkpoint_path):

        start_epoch, start_batch = (
            load_checkpoint(
                path=checkpoint_path,
                model=model,
                optimizer=optimizer,
            )
        )

    # =========================
    # Training
    # =========================

    last_yield_check_at = time.monotonic()

    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    for epoch in range(start_epoch, TOTAL_EPOCHS):

        model.train()

        # epoch에 따라 shuffle, 같은 epoch면 shuffle 순서 고정
        generator = torch.Generator()
        generator.manual_seed(random_state + epoch)

        train_loader = DataLoader(
            train_dataset,
            batch_size=BATCH_SIZE,
            shuffle=True,
            generator=generator,
        )

        for batch_index, (batch_features, batch_labels) in enumerate(train_loader):

            # checkpoint에서 복구한 epoch인 경우 이미 처리한 batch는 건너뜀
            if epoch == start_epoch and batch_index < start_batch:
                continue

            predictions = model(
                batch_features
            )

            loss = loss_fn(
                predictions,
                batch_labels,
            )

            optimizer.zero_grad()

            loss.backward()

            optimizer.step()

            # =========================
            # GPU preemption
            # =========================

            now = time.monotonic()

            if (
                    now - last_yield_check_at
                    >= YIELD_CHECK_INTERVAL_SECONDS
            ):
                last_yield_check_at = now

                if should_yield_gpu(task_id):

                    save_checkpoint(
                        path=checkpoint_path,
                        epoch=epoch,
                        batch_index=batch_index,
                        model=model,
                        optimizer=optimizer,
                    )

                    release_gpu(
                        task_id
                    )

                    acquire_gpu(
                        task_id=task_id,
                        task_type=GpuTaskType.TRAINING,
                        resume=True,
                    )

        start_batch = 0

    # =========================
    # Checkpoint cleanup
    # =========================

    if os.path.exists(checkpoint_path):
        os.remove(
            checkpoint_path
        )

    # =========================
    # Evaluation
    # =========================

    y_true, predictions = evaluate_model(
        algorithm=algorithm,
        model=model,
        test_loader=test_loader,
    )

    metrics = calculate_metrics(
        algorithm,
        y_true,
        predictions,
    )

    # =========================
    # Feature Importance
    # =========================

    task_type = TASK_TYPE_BY_ALGORITHM.get(algorithm)
    if task_type is None:
        raise NotValidTaskType("Algorithm not supported")

    baseline_metric = metrics["accuracy"] if task_type == ModelTaskType.CLASSIFICATION else metrics["rmse"]

    feature_importances = (
        calculate_feature_importance(
            model=model,
            test_loader=test_loader,
            raw_feature_columns=raw_feature_columns,
            encoded_feature_columns=encoded_feature_columns,
            task_type=task_type,
            baseline_metric=baseline_metric,
        )
    )


    # =========================
    # Artifact
    # =========================

    artifact = create_pytorch_artifact(
        algorithm=algorithm,
        model=model,
        input_size=input_size,
        hidden_size=HIDDEN_SIZE,
        raw_feature_columns=raw_feature_columns,
        encoded_feature_columns=encoded_feature_columns,
        num_classes=num_classes,
        target_categories=target_categories,
    )

    (
        artifact_uri,
        artifact_size,
        artifact_checksum,
    ) = save_pytorch_artifact(
        artifact=artifact,
        model_id=training_job.model_id,
    )

    # =========================
    # Result
    # =========================

    return TrainingResult(
        artifact_uri=artifact_uri,
        artifact_size=artifact_size,
        artifact_checksum=artifact_checksum,
        metrics=metrics,
        input_schema=create_input_schema(raw_features),
        feature_columns=raw_feature_columns,
        feature_importances=feature_importances,
    )