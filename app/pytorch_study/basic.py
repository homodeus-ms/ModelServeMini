import torch

def main() -> None:
    print("PyTorch version:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())

    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))

    x = torch.tensor(
        [1.0, 2.0, 3.0],
        device="cuda" if torch.cuda.is_available() else "cpu",
    )

    print("Tensor:", x)
    print("Device:", x.device)


if __name__ == "__main__":
    main()