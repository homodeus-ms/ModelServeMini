# ModelServeMini Quick Start

### Requirements

CPU Quick Start:

```text
Docker
Docker Compose
```

GPU / Kubernetes 환경:

```text
Linux
NVIDIA GPU
NVIDIA Driver
NVIDIA Container Toolkit
k3s
NVIDIA Device Plugin
CUDA-compatible environment
```

테스트 GPU:

```text
NVIDIA RTX 3090 24GB
```

---

### CPU Quick Start

GPU가 없는 환경에서도 CPU 기반 학습 / 추론 흐름을 실행할 수 있습니다.

#### 1. Repository Clone

```bash
git clone <repository-url>
cd ModelServeMini
```

#### 2. Environment 설정

Linux / macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

기본 Quick Start에서는 다음 설정을 사용합니다.

```env
ENABLE_GPU_TRAINING=false
```

따라서 학습 요청 시 CPU 알고리즘만 실행됩니다.

#### 3. 서비스 실행

```bash
docker compose up -d --build --scale cpu-worker=3
```

다음 서비스가 자동으로 실행됩니다.

```text
FastAPI
PostgreSQL
Kafka
Redis
CPU Worker × 3
Completion Worker
```

초기 실행 시 다음 작업도 자동 수행됩니다.

```text
PostgreSQL Table 생성
Test Member 생성 (member_id=1)
Kafka Topic 생성
```

Kafka Topics:

```text
training-jobs-cpu
training-jobs-gpu
training-job-completed
```

#### 4. 실행 상태 확인

```bash
docker compose ps
```

`db-init`, `kafka-init`은 초기화 완료 후 종료되므로 `Exited (0)` 상태가 정상입니다.

#### 5. Swagger

브라우저에서 다음 주소로 접속합니다.

```text
http://localhost:8000/docs
```

CPU Quick Start 환경에서 다음 흐름을 테스트할 수 있습니다.

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
Kafka 비동기 처리
    ↓
CPU Worker × 3
    ↓
Completion Worker
    ↓
Redis Pub/Sub
    ↓
SSE 진행 상태
    ↓
TrainingBatch 결과 조회
    ↓
ModelVersion 조회
    ↓
CPU Inference
```

#### 6. CPU End-to-End Test

```
(member_id 1번 사용 가능)
1. Dataset 생성
2. DatasetVersion 생성 (CSV 업로드)
3. DatasetVersion validate
4. Model 생성 (논리적 모델)
5. Training 요청
6. CPU 알고리즘 3개 Job 생성 확인
7. SSE 진행상황 확인(학습에 시간이 좀 걸리는 데이터셋이 필요함)
8. TrainingBatch 결과 확인
9. ModelVersion 확인, ModelVersion 한 개 선택, Deploy
10. CPU Inference
```


#### 7. 종료

데이터를 유지하면서 종료:

```bash
docker compose down
```

PostgreSQL Volume까지 삭제하여 완전히 초기화:

```bash
docker compose down -v
```

> `-v` 옵션은 PostgreSQL 데이터를 포함한 Docker Volume을 삭제하므로 초기화가 필요한 경우에만 사용합니다.

---
