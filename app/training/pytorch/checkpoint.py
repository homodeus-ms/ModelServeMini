import os

import torch
import torch.nn as nn


def get_checkpoint_path(
    training_job_id: int,
) -> str:

    return (
        "/app/storage/checkpoints/"
        f"training-{training_job_id}.pt"
    )


def save_checkpoint(
    path: str,
    epoch: int,
    batch_index: int,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
) -> None:

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    torch.save(
        {
            "epoch": epoch,
            "batch_index": batch_index,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
        },
        path,
    )


def load_checkpoint(
    path: str,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
) -> tuple[int, int]:

    checkpoint = torch.load(
        path,
        map_location="cuda",
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    optimizer.load_state_dict(
        checkpoint["optimizer_state_dict"]
    )

    epoch = checkpoint["epoch"]
    batch_index = checkpoint["batch_index"]

    print(
        f"Checkpoint loaded | "
        f"epoch={epoch + 1}, "
        f"batch={batch_index}"
    )

    return epoch, batch_index + 1