import torch.nn as nn


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


class MLPRegressor(nn.Module):

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
    ):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, x):
        return self.network(x)