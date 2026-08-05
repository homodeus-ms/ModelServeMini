-- ============================================================
-- 1. members
-- ============================================================

CREATE TABLE members (
    id BIGSERIAL PRIMARY KEY,

    email VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_members_email
        UNIQUE (email),

    CONSTRAINT ck_members_status
        CHECK (status IN (
            'ACTIVE',
            'INACTIVE'
        ))
);


-- ============================================================
-- 2. datasets
-- ============================================================

CREATE TABLE datasets (
    id BIGSERIAL PRIMARY KEY,

    created_by BIGINT NOT NULL,

    name VARCHAR(200) NOT NULL,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_datasets_created_by
        FOREIGN KEY (created_by)
        REFERENCES members(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_datasets_member_name
        UNIQUE (created_by, name),

    CONSTRAINT ck_datasets_name_not_blank
        CHECK (BTRIM(name) <> '')
);


-- ============================================================
-- 3. dataset_versions
-- ============================================================

CREATE TABLE dataset_versions (
    id BIGSERIAL PRIMARY KEY,

    dataset_id BIGINT NOT NULL,
    created_by BIGINT NOT NULL,

    version INTEGER NOT NULL,

    original_filename VARCHAR(255) NOT NULL,
    storage_uri TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    checksum VARCHAR(128),

    status VARCHAR(30) NOT NULL DEFAULT 'UPLOADING',

    row_count BIGINT,
    column_count INTEGER,

    schema_definition JSONB,
    validation_report JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_dataset_versions_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES datasets(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_dataset_versions_created_by
        FOREIGN KEY (created_by)
        REFERENCES members(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_dataset_versions_dataset_version
        UNIQUE (dataset_id, version),

    CONSTRAINT uq_dataset_versions_storage_uri
        UNIQUE (storage_uri),

    CONSTRAINT ck_dataset_versions_version_positive
        CHECK (version > 0),

    CONSTRAINT ck_dataset_versions_file_size
        CHECK (file_size >= 0),

    CONSTRAINT ck_dataset_versions_row_count
        CHECK (
            row_count IS NULL
            OR row_count >= 0
        ),

    CONSTRAINT ck_dataset_versions_column_count
        CHECK (
            column_count IS NULL
            OR column_count >= 0
        ),

    CONSTRAINT ck_dataset_versions_status
        CHECK (status IN (
            'UPLOADING',
            'UPLOADED',
            'VALIDATING',
            'READY',
            'INVALID',
            'FAILED'
        )),

    CONSTRAINT ck_dataset_versions_filename_not_blank
        CHECK (BTRIM(original_filename) <> ''),

    CONSTRAINT ck_dataset_versions_storage_uri_not_blank
        CHECK (BTRIM(storage_uri) <> '')
);


-- ============================================================
-- 4. models
-- ============================================================

CREATE TABLE models (
    id BIGSERIAL PRIMARY KEY,

    created_by BIGINT NOT NULL,

    name VARCHAR(200) NOT NULL,
    description TEXT,
    task_type VARCHAR(30) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_models_created_by
        FOREIGN KEY (created_by)
        REFERENCES members(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_models_member_name
        UNIQUE (created_by, name),

    CONSTRAINT ck_models_task_type
        CHECK (task_type IN (
            'CLASSIFICATION',
            'REGRESSION'
        )),

    CONSTRAINT ck_models_name_not_blank
        CHECK (BTRIM(name) <> '')
);


-- ============================================================
-- 5. training_jobs
-- ============================================================

CREATE TABLE training_jobs (
    id BIGSERIAL PRIMARY KEY,

    model_id BIGINT NOT NULL,
    dataset_version_id BIGINT NOT NULL,
    requested_by BIGINT NOT NULL,

    algorithm VARCHAR(50) NOT NULL,
    target_column VARCHAR(200) NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',

    training_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics JSONB,

    failure_message TEXT,

    queued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_training_jobs_model
        FOREIGN KEY (model_id)
        REFERENCES models(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_training_jobs_dataset_version
        FOREIGN KEY (dataset_version_id)
        REFERENCES dataset_versions(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_training_jobs_requested_by
        FOREIGN KEY (requested_by)
        REFERENCES members(id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_training_jobs_status
        CHECK (status IN (
            'PENDING',
            'RUNNING',
            'SUCCEEDED',
            'FAILED',
            'CANCELLED'
        )),

    CONSTRAINT ck_training_jobs_algorithm
        CHECK (algorithm IN (
            'LOGISTIC_REGRESSION',
            'RANDOM_FOREST_CLASSIFIER',
            'LINEAR_REGRESSION',
            'RANDOM_FOREST_REGRESSOR'
        )),

    CONSTRAINT ck_training_jobs_target_column_not_blank
        CHECK (BTRIM(target_column) <> ''),

    CONSTRAINT ck_training_jobs_started_at
        CHECK (
            started_at IS NULL
            OR started_at >= queued_at
        ),

    CONSTRAINT ck_training_jobs_finished_at
        CHECK (
            finished_at IS NULL
            OR (
                started_at IS NOT NULL
                AND finished_at >= started_at
            )
        ),

    CONSTRAINT ck_training_jobs_failure_message
        CHECK (
            status = 'FAILED'
            OR failure_message IS NULL
        )
);


-- ============================================================
-- 6. model_versions
-- ============================================================

CREATE TABLE model_versions (
    id BIGSERIAL PRIMARY KEY,

    model_id BIGINT NOT NULL,
    dataset_version_id BIGINT NOT NULL,

    version INTEGER NOT NULL,

    artifact_uri TEXT NOT NULL,
    artifact_size BIGINT,
    artifact_checksum VARCHAR(128),

    algorithm VARCHAR(50) NOT NULL,

    training_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    input_schema JSONB,
    feature_columns JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_model_versions_model
        FOREIGN KEY (model_id)
        REFERENCES models(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_model_versions_dataset_version
        FOREIGN KEY (dataset_version_id)
        REFERENCES dataset_versions(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_model_versions_training_job
        UNIQUE (training_job_id),

    CONSTRAINT uq_model_versions_model_version
        UNIQUE (model_id, version),

    CONSTRAINT uq_model_versions_artifact_uri
        UNIQUE (artifact_uri),

    CONSTRAINT ck_model_versions_version_positive
        CHECK (version > 0),

    CONSTRAINT ck_model_versions_artifact_size
        CHECK (
            artifact_size IS NULL
            OR artifact_size >= 0
        ),

    CONSTRAINT ck_model_versions_algorithm
        CHECK (algorithm IN (
            'LOGISTIC_REGRESSION',
            'RANDOM_FOREST_CLASSIFIER',
            'LINEAR_REGRESSION',
            'RANDOM_FOREST_REGRESSOR'
        )),

    CONSTRAINT ck_model_versions_artifact_uri_not_blank
        CHECK (BTRIM(artifact_uri) <> '')
);


------------------
-- 인덱스
------------------

-- 회원별 데이터셋 목록
CREATE INDEX idx_datasets_created_by_created_at
    ON datasets(created_by, created_at DESC);

-- 특정 데이터셋의 버전 목록
CREATE INDEX idx_dataset_versions_dataset_created_at
    ON dataset_versions(dataset_id, created_at DESC);

-- 검증 대기 또는 완료 상태 조회
CREATE INDEX idx_dataset_versions_status_created_at
    ON dataset_versions(status, created_at);

-- 회원별 모델 목록
CREATE INDEX idx_models_created_by_created_at
    ON models(created_by, created_at DESC);

-- 특정 모델의 학습 이력
CREATE INDEX idx_training_jobs_model_created_at
    ON training_jobs(model_id, created_at DESC);

-- 특정 데이터셋 버전을 사용한 학습 이력
CREATE INDEX idx_training_jobs_dataset_version
    ON training_jobs(dataset_version_id);

-- 회원이 요청한 학습 목록
CREATE INDEX idx_training_jobs_requested_by_created_at
    ON training_jobs(requested_by, created_at DESC);

-- Worker가 대기 작업을 조회할 때 사용
CREATE INDEX idx_training_jobs_pending_queue
    ON training_jobs(queued_at ASC)
    WHERE status = 'PENDING';

-- 특정 모델의 버전 목록
CREATE INDEX idx_model_versions_model_created_at
    ON model_versions(model_id, created_at DESC);

-- 특정 데이터셋 버전으로 만들어진 모델 검색
CREATE INDEX idx_model_versions_dataset_version
    ON model_versions(dataset_version_id);



-- MVP 1차 완료 후 테이블 추가
-- Training_job 세분화


CREATE TABLE training_job_model_versions (
    training_job_id BIGINT NOT NULL,
    relation_type VARCHAR(20) NOT NULL,
    model_version_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_training_job_model_versions
        PRIMARY KEY (training_job_id, relation_type),

    CONSTRAINT fk_training_job_model_versions_training_job
        FOREIGN KEY (training_job_id)
        REFERENCES training_jobs(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_training_job_model_versions_model_version
        FOREIGN KEY (model_version_id)
        REFERENCES model_versions(id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_training_job_model_versions_relation_type
        CHECK (relation_type IN ('BASE', 'RESULT'))
);


CREATE UNIQUE INDEX uq_training_job_model_versions_result
    ON training_job_model_versions(model_version_id)
    WHERE relation_type = 'RESULT';


CREATE INDEX ix_training_job_model_versions_model_version_id
    ON training_job_model_versions(model_version_id);


CREATE TABLE training_attempts (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY,
    training_job_id BIGINT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL,

    kubernetes_job_name VARCHAR(255),
    pod_name VARCHAR(255),
    gpu_node_name VARCHAR(255),
    gpu_type VARCHAR(100),

    checkpoint_uri TEXT,
    log_uri TEXT,

    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,

    exit_code INTEGER,
    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_training_attempts
        PRIMARY KEY (id),

    CONSTRAINT fk_training_attempts_training_job
        FOREIGN KEY (training_job_id)
        REFERENCES training_jobs(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_training_attempts_job_attempt
        UNIQUE (training_job_id, attempt_number),

    CONSTRAINT ck_training_attempts_attempt_number
        CHECK (attempt_number > 0),

    CONSTRAINT ck_training_attempts_status
        CHECK (
            status IN (
                'PENDING',
                'RUNNING',
                'SUCCEEDED',
                'FAILED',
                'CANCELLED'
            )
        )
);


CREATE INDEX ix_training_attempts_status_started_at
    ON training_attempts(status, started_at);


CREATE INDEX ix_training_attempts_training_job_id
    ON training_attempts(training_job_id);