import torch
import torch.nn as nn

def main() -> None:
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("device:", device)

    # y = 2x 데이터 학습
    x = torch.tensor([[1.0], [2.0], [3.0], [4.0]], device=device)
    y = torch.tensor([[2.0], [4.0], [6.0], [8.0]], device=device)

    # y = wx + b 형태의 모델
    model = nn.Linear(in_features=1, out_features=1).to(device)

    # 평균 제곱 오차, 함수객체임
    loss_fn = nn.MSELoss()

    # 모델의 weight, bias를 수정하는 역할
    # SGD : 확률적 경사 하강법
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    for epoch in range(1000):
        # 1. 순전파
        prediction = model(x)

        # 2. 오차 계산
        loss = loss_fn(prediction, y)

        # 3. 이전 gradient 제거
        optimizer.zero_grad()

        # 4. 미분 -> gradient 계산
        loss.backward()

        # 5. weight, bias 갱신
        optimizer.step()

        if epoch % 100 == 0:
            print(f"epoch: {epoch}, loss: {loss.item():.6f}")

    print("weight:", model.weight.item())
    print("bias:", model.bias.item())

    test_x = torch.tensor([[5.0]], device=device)
    prediction = model(test_x)
    print("x=5 prediction:", prediction.item())

if __name__ == "__main__":
    main()