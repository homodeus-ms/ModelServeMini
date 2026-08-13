# ModelServeMini GPU / Kubernetes Setup

ModelServeMini의 GPU Training / Inference 환경을 k3s 기반으로 구성하는 방법입니다.

CPU 기능만 테스트하려면 GPU 환경은 필요하지 않습니다.  
CPU 환경은 [Quick Start](quick-start.md)를 참고하세요.

---

### 1. Test Environment

본 프로젝트는 다음 환경에서 테스트했습니다.

```text
OS                  Ubuntu 24.04 (WSL2)
Kubernetes          k3s v1.36.3+k3s1
Container Runtime   containerd
GPU                 NVIDIA RTX 3090 24GB
NVIDIA Toolkit      1.19.1
Device Plugin       0.19.3
```

GPU 환경에서 다음 기능을 실행할 수 있습니다.

```text
GPU Training
GPU Inference
Priority GPU Scheduler
Training Preemption / Checkpoint / Resume
```

---

### 2. Prerequisites

필요 환경:

```text
Linux
NVIDIA GPU
NVIDIA Driver
NVIDIA Container Toolkit
k3s
Helm
NVIDIA Device Plugin
```

먼저 GPU가 정상적으로 인식되는지 확인합니다.

```bash
nvidia-smi
```

---

### 3. NVIDIA Container Toolkit 설치

NVIDIA Container Toolkit 공식 repository를 등록합니다.

```bash
sudo apt-get update

sudo apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg2
```

NVIDIA repository 등록:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor \
  -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L \
  https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

Package 목록 갱신:

```bash
sudo apt-get update
```

본 프로젝트에서 테스트한 버전:

```bash
export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.19.1-1

sudo apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}
```

설치 확인:

```bash
nvidia-container-cli --version
```

```bash
dpkg -l | grep nvidia-container
```

---

### 4. k3s 설치

k3s 설치:

```bash
curl -sfL https://get.k3s.io | sh -
```

Node 확인:

```bash
sudo k3s kubectl get nodes -o wide
```

정상적인 경우 Node가 `Ready` 상태로 표시됩니다.

```text
NAME   STATUS   ROLES
kiwi   Ready    control-plane
```

---

### 5. NVIDIA Runtime 구성

NVIDIA Container Toolkit을 containerd Runtime에 연결합니다.

```bash
sudo nvidia-ctk runtime configure --runtime=containerd
```

> k3s는 자체 containerd 설정을 사용하므로 실제 환경에서는
> k3s가 NVIDIA Runtime을 인식하는지 반드시 아래 명령으로 확인합니다.

k3s 재시작:

```bash
sudo systemctl restart k3s
```

Runtime 확인:

```bash
sudo cat /var/lib/rancher/k3s/agent/etc/containerd/config.toml \
  | grep -i -A 10 nvidia
```

다음과 같은 설정이 확인되어야 합니다.

```text
[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.'nvidia']
  runtime_type = "io.containerd.runc.v2"

[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.'nvidia'.options]
  BinaryName = "/usr/bin/nvidia-container-runtime"
```

---

### 6. NVIDIA Device Plugin 설치

Helm repository 등록:

```bash
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo update
```

Namespace 생성:

```bash
sudo k3s kubectl create namespace nvidia-device-plugin
```

본 프로젝트에서는 하나의 RTX 3090을 Training과 Inference가 공유할 수 있도록
NVIDIA Device Plugin의 Time-Slicing을 사용합니다.

```bash
sudo helm upgrade --install nvdp nvdp/nvidia-device-plugin \
  --namespace nvidia-device-plugin \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  --set runtimeClassName=nvidia \
  --set config.default=default \
  --set-json 'config.map.default={"version":"v1","flags":{"migStrategy":"none"},"sharing":{"timeSlicing":{"resources":[{"name":"nvidia.com/gpu","replicas":2}]}}}'
```

구조:

```text
RTX 3090 (Physical GPU × 1)
        │
        │ Time-Slicing
        ▼
nvidia.com/gpu × 2
        │
        ├── GPU Training
        │
        └── GPU Inference
```

> `replicas: 2`는 물리 GPU가 2개라는 의미가 아닙니다.
> 하나의 물리 GPU를 Kubernetes에 2개의 공유 가능한 GPU Resource로 노출합니다.

설치 확인:

```bash
sudo helm list -A \
  --kubeconfig /etc/rancher/k3s/k3s.yaml
```

Device Plugin 확인:

```bash
sudo k3s kubectl get pods -A | grep -i nvidia
```

GPU Resource 확인:

```bash
sudo k3s kubectl get node \
  -o jsonpath='{.items[0].status.capacity.nvidia\.com/gpu}'

echo
```

본 프로젝트에서는 다음 값이 출력됩니다.

```text
2
```

---

### 7. GPU Test Pod

실제 Kubernetes Pod에서 GPU를 사용할 수 있는지 확인합니다.

`k8s/gpu-test.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test

spec:
  runtimeClassName: nvidia
  restartPolicy: Never

  containers:
    - name: gpu-test
      image: nvidia/cuda:13.0.0-base-ubuntu24.04

      command:
        - nvidia-smi

      resources:
        limits:
          nvidia.com/gpu: 1
```

실행:

```bash
sudo k3s kubectl apply -f k8s/gpu-test.yaml
```

확인:

```bash
sudo k3s kubectl get pods
sudo k3s kubectl logs gpu-test
```

Pod 내부에서 `nvidia-smi`가 정상적으로 출력되면 GPU Runtime 구성이 완료된 것입니다.

테스트 후:

```bash
sudo k3s kubectl delete pod gpu-test
```

---

### 8. ModelServeMini Image 등록

현재 프로젝트는 별도 Container Registry 대신 Docker에서 빌드한 Local Image를
k3s containerd에 직접 등록합니다.

ModelServeMini에서는 일반 Python 서비스와 GPU 서비스를 각각 공통 Image로 빌드한 뒤,
각 Kubernetes Deployment에서 사용하는 Image 이름으로 Tag를 생성합니다.

#### 일반 Python Image

FastAPI, CPU Worker, Completion Worker, GPU Scheduler는 기본 `Dockerfile`을 사용합니다.

공통 Image 빌드:

```bash
docker build \
  -f Dockerfile \
  -t modelservemini-base:latest .
```

각 Kubernetes Deployment에서 사용할 Image Tag를 생성합니다.

```bash
docker tag modelservemini-base:latest modelservemini-api:latest
docker tag modelservemini-base:latest modelservemini-cpu-worker:latest
docker tag modelservemini-base:latest modelservemini-completion-worker:latest
docker tag modelservemini-base:latest modelservemini-gpu-scheduler:latest
```

Image를 하나의 tar 파일로 저장합니다.

```bash
docker save \
  modelservemini-api:latest \
  modelservemini-cpu-worker:latest \
  modelservemini-completion-worker:latest \
  modelservemini-gpu-scheduler:latest \
  -o modelservemini-base.tar
```

k3s containerd에 등록합니다.

```bash
sudo k3s ctr -n k8s.io images import \
  modelservemini-base.tar
```

#### GPU Image

GPU Worker와 GPU Inference는 `Dockerfile.gpu`를 사용합니다.

공통 GPU Image 빌드:

```bash
docker build \
  -f Dockerfile.gpu \
  -t modelservemini-gpu-base:latest .
```

GPU Worker와 GPU Inference에서 사용할 Image Tag를 생성합니다.

```bash
docker tag modelservemini-gpu-base:latest modelservemini-gpu-worker:latest
docker tag modelservemini-gpu-base:latest modelservemini-gpu-inference:latest
```

Image를 하나의 tar 파일로 저장합니다.

```bash
docker save \
  modelservemini-gpu-worker:latest \
  modelservemini-gpu-inference:latest \
  -o modelservemini-gpu.tar
```

k3s containerd에 등록합니다.

```bash
sudo k3s ctr -n k8s.io images import \
  modelservemini-gpu.tar
```

#### Image 등록 확인

```bash
sudo k3s ctr -n k8s.io images list \
  | grep modelservemini
```

다음 Image들이 등록되어 있어야 합니다.

```text
modelservemini-api:latest
modelservemini-cpu-worker:latest
modelservemini-completion-worker:latest
modelservemini-gpu-scheduler:latest
modelservemini-gpu-worker:latest
modelservemini-gpu-inference:latest
```

Kubernetes Deployment에서는 Local Image를 사용하므로 다음 설정을 사용합니다.

```yaml
imagePullPolicy: Never
```

따라서 k3s containerd에 등록된 Image 이름과 각 Deployment YAML의 `image` 이름이
정확히 일치해야 합니다.

> 다른 환경에서는 Image를 직접 빌드하여 containerd에 import하거나
> Container Registry를 사용할 수 있습니다.

---
---

### 9. Kubernetes Components

GPU 환경에서는 다음 구성요소가 실행됩니다.

```text
FastAPI
    │
    ├── Kafka
    │     ├── CPU Worker × 3
    │     ├── GPU Worker
    │     └── Completion Worker
    │
    ├── Redis
    │
    └── GPU Inference
            │
            └── GPU Scheduler
```

주요 Pod:

```text
api
cpu-worker × 3
gpu-worker
gpu-inference
gpu-scheduler
completion-worker
kafka
redis
```

현재 PostgreSQL은 Docker Container로 실행합니다.

---

### 10. Kubernetes Service Communication

Pod 간 통신에는 Kubernetes Service DNS를 사용합니다.

```text
Kafka          kafka:9092
Redis          redis:6379
GPU Scheduler  gpu-scheduler:<service-port>
GPU Inference  gpu-inference:8001
```

예를 들어 FastAPI Pod에서 GPU Inference Pod를 호출할 때:

```text
http://localhost:8001
```

을 사용하면 안 됩니다.

Pod마다 독립적인 Network Namespace를 사용하므로 `localhost`는
FastAPI Pod 자신을 의미합니다.

따라서:

```text
http://gpu-inference:8001
```

처럼 Kubernetes Service 이름을 사용합니다.

API Deployment 예:

```yaml
- name: GPU_INFERENCE_URL
  value: "http://gpu-inference:8001"
```

---

### 11. ModelServeMini 배포

현재 구성에서는 PostgreSQL만 Docker Compose로 실행합니다.

```bash
docker compose up -d db
```

Kubernetes Resource 적용:

```bash
sudo k3s kubectl apply -f k8s/
```

Pod 확인:

```bash
sudo k3s kubectl get pods
```

정상 실행 상태:

```text
api                 Running
cpu-worker × 3      Running
gpu-worker          Running
gpu-inference       Running
gpu-scheduler       Running
completion-worker   Running
kafka               Running
redis               Running
```

---

### 12. FastAPI 접속

Service 확인:

```bash
sudo k3s kubectl get svc api
```

Port Forward:

```bash
sudo k3s kubectl port-forward service/api 8000:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

Port Forward 종료:

```text
Ctrl + C
```

---

### 13. End-to-End Test

GPU 환경에서 다음 전체 흐름을 테스트할 수 있습니다.

```text
Dataset 생성
    ↓
DatasetVersion CSV 업로드
    ↓
DatasetVersion 검증
    ↓
Model 생성
    ↓
Training 요청
    ↓
Kafka
    ├── CPU Training
    └── GPU Training
            ↓
      GPU Scheduler
    ↓
Completion Worker
    ↓
Redis Pub/Sub
    ↓
SSE
    ↓
TrainingBatch 결과
    ↓
ModelVersion
    ↓
Deploy
    ↓
Inference
    ├── CPU Inference
    └── GPU Inference
            ↓
      GPU Scheduler
```

GPU Training 중 GPU Inference 요청을 발생시켜 다음 흐름도 테스트할 수 있습니다.

```text
GPU Training
    ↓
Checkpoint
    ↓
GPU Release
    ↓
Inference 우선 실행
    ↓
GPU Release
    ↓
Training Resume
```

---

### 14. Troubleshooting

#### Insufficient nvidia.com/gpu

```text
0/1 nodes are available:
1 Insufficient nvidia.com/gpu
```

GPU Resource 사용 상태 확인:

```bash
sudo k3s kubectl describe node
```

GPU Pod 확인:

```bash
sudo k3s kubectl get pods
```

테스트용 `gpu-test` Pod 등이 GPU Resource를 사용 중이라면 삭제합니다.

```bash
sudo k3s kubectl delete pod gpu-test
```

---

#### ErrImageNeverPull

```text
ErrImageNeverPull
```

k3s containerd에 Image가 존재하는지 확인합니다.

```bash
sudo k3s ctr -n k8s.io images list
```

필요한 경우:

```bash
sudo k3s ctr -n k8s.io images import <image>.tar
```

Deployment의 `image:` 이름과 실제 등록된 Image 이름도 정확히 일치해야 합니다.

---

#### Connection refused

```text
httpx.ConnectError: [Errno 111] Connection refused
```

다른 Pod에 접근하면서 `localhost`를 사용하지 않았는지 확인합니다.

```text
gpu-inference:8001
kafka:9092
redis:6379
```

와 같이 Kubernetes Service DNS를 사용합니다.

---

#### Port Forward Port 충돌

```text
bind: address already in use
```

다른 Host Port를 사용할 수 있습니다.

```bash
sudo k3s kubectl port-forward service/api 8002:8000
```

이 경우:

```text
http://localhost:8002/docs
```

로 접속합니다.

---

### 15. Notes

현재 Kubernetes 환경은 로컬 단일 Node 환경에서
GPU Resource Scheduling 구조를 검증하기 위한 구성입니다.

```text
Single Node k3s
RTX 3090
NVIDIA Device Plugin Time-Slicing
Redis Priority GPU Scheduler
Kafka Async Training Workers
PyTorch Checkpoint / Preemption / Resume
```

Production 환경에서는 추가적으로 다음 요소를 고려할 수 있습니다.

```text
Container Registry
PersistentVolume / PersistentVolumeClaim
Object Storage (S3 / MinIO)
Multi-node GPU Scheduling
Authentication / Authorization
Monitoring / Observability
```