import cudf
import os
import torch
import torch.nn as nn

from torch.utils.data import DataLoader, TensorDataset
from cuml.model_selection import train_test_split

from app.db.session import SessionLocal
from app.domain.dataset_version.model import DatasetVersion
from app.domain.training_job.model import TrainingJob
from app.training.artifact_storage import save_pytorch_artifact
from app.training.result import TrainingResult
from app.training.utils import resolve_dataset_path
from app.domain.training_job import repository as training_job_repository
from app.domain.dataset_version import repository as dataset_version_repository

from app.gpu_scheduler.client import (
    should_yield_gpu,
    release_gpu,
    acquire_gpu,
)
from app.gpu_scheduler.schema import GpuTaskType


def get_checkpoint_path(training_job_id: int) -> str:
    return f"/app/storage/checkpoints/training-{training_job_id}.pt"

def get_task_id(training_job_id: int) -> str:
    return f"training-{training_job_id}"

class MLPClassifier(nn.Module):

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_classes: int,
    ):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, num_classes),
        )

    def forward(self, x):
        return self.network(x)


def prepare_training_data(
    dataframe: cudf.DataFrame,
    target_column: str,
    batch_size: int,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[DataLoader, DataLoader, int, int, list[str], list]:

    features = dataframe.drop(columns=[target_column])
    target = dataframe[target_column]

    # categorical feature → One-Hot
    features = cudf.get_dummies(features, dummy_na=False)

    # target → 0, 1, 2...
    target_codes, target_categories = target.factorize()

    encoded_feature_columns = list(features.columns)

    target_category_list = target_categories.to_arrow().to_pylist()

    # cuDF / CuPy 상태에서 train/test 분리
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target_codes,
        test_size=test_size,
        random_state=random_state,
    )

    # GPU Tensor 변환
    x_train_tensor = torch.as_tensor(x_train.to_cupy(), device="cuda", dtype=torch.float32)
    x_test_tensor = torch.as_tensor(x_test.to_cupy(), device="cuda", dtype=torch.float32)
    y_train_tensor = torch.as_tensor(y_train, device="cuda", dtype=torch.long)
    y_test_tensor = torch.as_tensor(y_test, device="cuda", dtype=torch.long)

    input_size = x_train_tensor.shape[1]
    num_classes = len(target_category_list)

    train_dataset = TensorDataset(x_train_tensor, y_train_tensor)
    test_dataset = TensorDataset(x_test_tensor, y_test_tensor)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return (
        train_loader,
        test_loader,
        input_size,
        num_classes,
        encoded_feature_columns,
        target_category_list,
    )



def train(training_job: TrainingJob, dataset_ver: DatasetVersion) -> TrainingResult:

    task_id = get_task_id(training_job.id)
    checkpoint_path = get_checkpoint_path(training_job.id)

    dataset_path = resolve_dataset_path(dataset_ver.storage_uri)
    dataframe = cudf.read_csv(dataset_path)

    print("dataframe rows:", len(dataframe))
    print("dataframe columns:", len(dataframe.columns))

    (
        train_loader,
        test_loader,
        input_size,
        num_classes,
        encoded_feature_columns,
        target_categories,
    ) = prepare_training_data(
        dataframe=dataframe,
        target_column=training_job.target_column,
        batch_size=64,
        test_size=training_job.training_config.get(
            "test_size",
            0.2,
        ),
        random_state=training_job.training_config.get(
            "random_state",
            42,
        ),
    )

    print("input_size:", input_size)
    print("num_classes:", num_classes)

    model = MLPClassifier(input_size=input_size, hidden_size=128, num_classes=num_classes).to("cuda")

    loss_fn = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)


    # 프로세스 종료 후 다시 시작했을 때 재개를 위해

    start_epoch = 0
    start_batch = 0
    checkpoint_path = get_checkpoint_path(training_job.id)

    if os.path.exists(checkpoint_path):
        start_epoch, start_batch = load_checkpoint(
            path=checkpoint_path,
            model=model,
            optimizer=optimizer,
        )


    YIELD_CHECK_INTERVAL = 30

    for epoch in range(start_epoch, 5):

        total_loss = 0.0

        for batch_index, (batch_features, batch_labels) in enumerate(train_loader):

            # 이미 처리한 부분 건너뛰기
            if epoch == start_epoch and batch_index < start_batch:
                continue

            logits = model(batch_features)
            loss = loss_fn(logits, batch_labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()


            total_loss += loss.item()

            if batch_index % YIELD_CHECK_INTERVAL == 0 and should_yield_gpu(task_id):

                print(f"Preemption requested | " f"epoch={epoch + 1}, " f"batch={batch_index}")

                # 현재는 메모리에 정보가 남아있으므로 resume을 위해 딱히 load가 필요하진 않음.
                save_checkpoint(path=checkpoint_path, epoch=epoch, batch_index=batch_index, model=model, optimizer=optimizer)

                release_gpu(task_id)

                print("GPU released. " "Waiting for resume...")

                acquire_gpu(task_id=task_id, task_type=GpuTaskType.TRAINING, resume=True)

                print("GPU reacquired. " "Resume training.")


        start_batch = 0


    # 학습이 끝나면 저장했던 checkpoint는 삭제
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)


    accuracy = calculate_accuracy(model=model, data_loader=test_loader)
    metrics = {"accuracy": accuracy}

    artifact = {
        "model_state_dict": model.state_dict(),

        "input_size": input_size,
        "hidden_size": 128,
        "num_classes": num_classes,

        "feature_columns": encoded_feature_columns,
        "target_categories": target_categories,

        "task_type": "CLASSIFICATION",
    }

    artifact_uri, artifact_size, artifact_checksum = (
        save_pytorch_artifact(
            artifact=artifact,
            model_id=training_job.model_id,
        )
    )

    result = TrainingResult(
        artifact_uri=artifact_uri,
        artifact_size=artifact_size,
        artifact_checksum=artifact_checksum,

        metrics=metrics,

        input_schema={
            "feature_columns": encoded_feature_columns,
            "target_categories": target_categories,
        },

        feature_columns=encoded_feature_columns,

        # PyTorch feature importance는 아직 미구현
        feature_importances=[],
    )

    return result



def save_checkpoint(path: str, epoch: int, batch_index: int,
                    model: nn.Module, optimizer: torch.optim.Optimizer) -> None:

    os.makedirs(os.path.dirname(path), exist_ok=True)

    torch.save(
        {
            "epoch": epoch,
            "batch_index": batch_index,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
        },
        path,
    )

def load_checkpoint(path: str, model: nn.Module, optimizer: torch.optim.Optimizer) -> tuple[int, int]:

    checkpoint = torch.load(path, map_location="cuda")
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    epoch = checkpoint["epoch"]
    batch_index = checkpoint["batch_index"]

    print(f"Checkpoint loaded | " f"epoch={epoch + 1}, " f"batch={batch_index}")

    return epoch, batch_index + 1


def calculate_accuracy(model: nn.Module, data_loader: DataLoader) -> float:

    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():

        for batch_features, batch_labels in data_loader:

            logits = model(batch_features)

            predictions = torch.argmax(logits, dim=1)

            correct += (predictions == batch_labels).sum().item()

            total += batch_labels.size(0)

    return correct / total

