# CI/CD & GitOps

ModelServeMini는 GitHub Actions, Docker Hub, Helm, Argo CD를 이용해
코드 변경부터 Kubernetes 배포까지 자동화했습니다.

## 1. CI/CD Flow

```text
Feature Branch
      ↓
Pull Request
      ↓
GitHub Actions Test
      ↓
Merge to main
      ↓
CPU / GPU Docker Image Build & Push
      ↓
Deploy Repository Helm Image Tag Update
      ↓
Argo CD Sync
      ↓
Kubernetes Deployment
```

Application Repository와 Deployment Repository를 분리했습니다.

- `ModelServeMini`: 애플리케이션 코드, 테스트, Dockerfile, GitHub Actions
- `ModelServeMini-deploy`: Helm Chart 및 Kubernetes 배포 설정

Pull Request에서는 테스트만 수행하고, main에 반영된 경우 Docker Image를 빌드하여 Docker Hub에 Push합니다.

Image Tag에는 Git Commit SHA를 사용하여 코드와 배포 이미지의 버전을 추적할 수 있도록 했습니다.

---

## 2. GitOps with Argo CD

GitHub Actions는 새로운 Docker Image를 생성한 후
`ModelServeMini-deploy`의 Helm Image Tag를 갱신합니다.

Argo CD는 해당 Repository를 Desired State로 사용하여 Kubernetes Cluster와 동기화합니다.

```text
ModelServeMini
      ↓
GitHub Actions
      ↓
Docker Hub + ModelServeMini-deploy
                    ↓
                 Argo CD
                    ↓
             Kubernetes Cluster
```

이를 통해 애플리케이션 Repository에서 Kubernetes를 직접 변경하지 않고,
Git을 Single Source of Truth로 사용하는 GitOps 방식으로 배포합니다.

---

## 3. Docker Image Build 최적화

CPU / GPU 환경의 Dependency 차이가 크기 때문에 Docker Image를 분리했습니다.

특히 초기 GPU Image는 CI마다 PyTorch, RAPIDS 등의 대용량 Dependency를 처리하면서
전체 CI에 약 8~14분이 소요되었습니다.

GPU Dependency는 변경 빈도가 낮기 때문에 별도의 Base Image로 분리했습니다.

```text
modelservemini-gpu-base
├─ PyTorch / CUDA
├─ RAPIDS
└─ GPU Dependencies
          ↓
modelservemini-gpu:<git-sha>
└─ Application
```

또한 CPU Image에서 불필요한 GPU Dependency를 제거했습니다.

그 결과 전체 CI 실행 시간을 **약 8~14분 → 약 4분대**로 단축했습니다.

---

## 4. Kafka Persistence & Initialization

Kubernetes 재시작 이후 Kafka Topic이 유실되어 Worker에서
`UNKNOWN_TOPIC_OR_PARTITION` 오류가 발생했습니다.

Kafka의 실제 데이터 경로가 PVC를 사용하지 않고 있음을 확인하고,
`KAFKA_LOG_DIRS`를 PVC Mount Path에 연결하여 Kafka 데이터를 영속화했습니다.

```yaml
- name: KAFKA_LOG_DIRS
  value: {{ .Values.kafka.storage.mountPath | quote }}
```

또한 Kafka Topic 생성 Job을 Argo CD `PostSync` Hook으로 구성하여
배포 시 필요한 Topic이 자동으로 초기화되도록 했습니다.

```yaml
annotations:
  argocd.argoproj.io/hook: PostSync
  argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
```

두 설정의 역할은 다음과 같습니다.

```text
Kafka PVC       → Broker / Topic 데이터 유지
PostSync Hook   → 배포 시 필요한 Topic 초기화
```

---

## 5. Result

최종적으로 다음 과정을 자동화했습니다.

```text
Code
 ↓
Test
 ↓
Docker Image Build
 ↓
Docker Hub
 ↓
Helm Image Tag Update
 ↓
Argo CD
 ↓
Kubernetes
```

이를 통해 코드 변경에 대한 검증부터 Docker Image 생성,
Kubernetes 배포까지 자동화하고 Git을 기준으로 배포 상태를 관리하도록 구성했습니다.