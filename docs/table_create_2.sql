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
        CHECK (
            status IN (
                'ACTIVE',
                'INACTIVE'
            )
        )
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
        CHECK (
            status IN (
                'UPLOADING',
                'UPLOADED',
                'VALIDATING',
                'READY',
                'INVALID',
                'FAILED'
            )
        ),

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
        CHECK (
            task_type IN (
                'CLASSIFICATION',
                'REGRESSION'
            )
        ),

    CONSTRAINT ck_models_name_not_blank
        CHECK (BTRIM(name) <> '')
);


-- ============================================================
-- 5. training_batches
-- 한 번의 사용자 학습 요청 단위
-- ============================================================

CREATE TABLE training_batches (
    id UUID PRIMARY KEY,

    requested_by BIGINT NOT NULL,
    dataset_version_id BIGINT NOT NULL,

    target_column VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',

    total_jobs INTEGER NOT NULL,
    completed_jobs INTEGER NOT NULL DEFAULT 0,

    recommendation JSONB,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_training_batches_requested_by
        FOREIGN KEY (requested_by)
        REFERENCES members(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_training_batches_dataset_version
        FOREIGN KEY (dataset_version_id)
        REFERENCES dataset_versions(id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_training_batches_target_column_not_blank
        CHECK (BTRIM(target_column) <> ''),

    CONSTRAINT ck_training_batches_job_count
        CHECK (
            total_jobs > 0
            AND completed_jobs >= 0
            AND completed_jobs <= total_jobs
        ),

    CONSTRAINT ck_training_batches_status
        CHECK (
            status IN (
                'PENDING',
                'RUNNING',
                'SUCCEEDED',
                'FAILED',
                'CANCELLED'
            )
        ),

    CONSTRAINT ck_training_batches_task_type
        CHECK (
            task_type IN (
                'CLASSIFICATION',
                'REGRESSION'
            )
        )
);


-- ============================================================
-- 6. training_jobs
-- 알고리즘 하나당 하나의 실제 학습 작업
-- ============================================================

CREATE TABLE training_jobs (
    id BIGSERIAL PRIMARY KEY,

    training_batch_id UUID NOT NULL,

    model_id BIGINT NOT NULL,
    dataset_version_id BIGINT NOT NULL,
    requested_by BIGINT NOT NULL,

    algorithm VARCHAR(50) NOT NULL,
    target_column VARCHAR(200) NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',

    completion_counted BOOLEAN NOT NULL DEFAULT FALSE,

    training_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics JSONB,

    failure_message TEXT,

    queued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_training_jobs_training_batch
        FOREIGN KEY (training_batch_id)
        REFERENCES training_batches(id)
        ON DELETE RESTRICT,

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
        CHECK (
            status IN (
                'PENDING',
                'RUNNING',
                'SUCCEEDED',
                'FAILED',
                'CANCELLED'
            )
        ),

    CONSTRAINT ck_training_jobs_algorithm
        CHECK (
            algorithm IN (
                'LOGISTIC_REGRESSION',
                'RANDOM_FOREST_CLASSIFIER',
                'LINEAR_REGRESSION',
                'RANDOM_FOREST_REGRESSOR',
                'GRADIENT_BOOSTING_CLASSIFIER',
                'GRADIENT_BOOSTING_REGRESSOR',
                'XGBOOST_CLASSIFIER_GPU',
                'XGBOOST_REGRESSOR_GPU'
            )
        ),

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
-- 7. model_versions
-- 실제 학습 결과 artifact
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
    feature_importances JSONB,

    deployment_status VARCHAR(30) NOT NULL DEFAULT 'NONE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_model_versions_model
        FOREIGN KEY (model_id)
        REFERENCES models(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_model_versions_dataset_version
        FOREIGN KEY (dataset_version_id)
        REFERENCES dataset_versions(id)
        ON DELETE RESTRICT,

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
        CHECK (
            algorithm IN (
                'LOGISTIC_REGRESSION',
                'RANDOM_FOREST_CLASSIFIER',
                'LINEAR_REGRESSION',
                'RANDOM_FOREST_REGRESSOR',
                'GRADIENT_BOOSTING_CLASSIFIER',
                'GRADIENT_BOOSTING_REGRESSOR',
                'XGBOOST_CLASSIFIER_GPU',
                'XGBOOST_REGRESSOR_GPU'
            )
        ),

    CONSTRAINT ck_model_versions_deployment_status
        CHECK (
            deployment_status IN (
                'NONE',
                'PRODUCTION',
                'ARCHIVED'
            )
        ),

    CONSTRAINT ck_model_versions_artifact_uri_not_blank
        CHECK (BTRIM(artifact_uri) <> '')
);


-- ============================================================
-- 8. training_job_model_versions
-- TrainingJob과 ModelVersion의 BASE / RESULT 관계
-- ============================================================

CREATE TABLE training_job_model_versions (
    training_job_id BIGINT NOT NULL,
    relation_type VARCHAR(20) NOT NULL,
    model_version_id BIGINT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_training_job_model_versions
        PRIMARY KEY (
            training_job_id,
            relation_type
        ),

    CONSTRAINT fk_training_job_model_versions_training_job
        FOREIGN KEY (training_job_id)
        REFERENCES training_jobs(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_training_job_model_versions_model_version
        FOREIGN KEY (model_version_id)
        REFERENCES model_versions(id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_training_job_model_versions_relation_type
        CHECK (
            relation_type IN (
                'BASE',
                'RESULT'
            )
        )
);


-- 하나의 ModelVersion은 최대 하나의 TrainingJob 결과로만 생성
CREATE UNIQUE INDEX uq_training_job_model_versions_result
    ON training_job_model_versions(model_version_id)
    WHERE relation_type = 'RESULT';


-- ============================================================
-- 9. training_attempts
-- TrainingJob의 실제 실행 attempt
-- ============================================================

CREATE TABLE training_attempts (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

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

    CONSTRAINT fk_training_attempts_training_job
        FOREIGN KEY (training_job_id)
        REFERENCES training_jobs(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_training_attempts_job_attempt
        UNIQUE (
            training_job_id,
            attempt_number
        ),

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
        ),

    CONSTRAINT ck_training_attempts_finished_at
        CHECK (
            finished_at IS NULL
            OR (
                started_at IS NOT NULL
                AND finished_at >= started_at
            )
        )
);


-- ============================================================
-- 10. indexes
-- ============================================================

-- datasets
CREATE INDEX idx_datasets_created_by_created_at
    ON datasets(created_by, created_at DESC);


-- dataset_versions
CREATE INDEX idx_dataset_versions_dataset_created_at
    ON dataset_versions(dataset_id, created_at DESC);

CREATE INDEX idx_dataset_versions_status_created_at
    ON dataset_versions(status, created_at);


-- models
CREATE INDEX idx_models_created_by_created_at
    ON models(created_by, created_at DESC);


-- training_batches
CREATE INDEX idx_training_batches_requested_by_created_at
    ON training_batches(requested_by, created_at DESC);

CREATE INDEX idx_training_batches_status_created_at
    ON training_batches(status, created_at);


-- training_jobs
CREATE INDEX idx_training_jobs_training_batch_id
    ON training_jobs(training_batch_id);

CREATE INDEX idx_training_jobs_model_created_at
    ON training_jobs(model_id, created_at DESC);

CREATE INDEX idx_training_jobs_dataset_version
    ON training_jobs(dataset_version_id);

CREATE INDEX idx_training_jobs_requested_by_created_at
    ON training_jobs(requested_by, created_at DESC);

CREATE INDEX idx_training_jobs_status
    ON training_jobs(status);

CREATE INDEX idx_training_jobs_pending_queue
    ON training_jobs(queued_at ASC)
    WHERE status = 'PENDING';


-- model_versions
CREATE INDEX idx_model_versions_model_created_at
    ON model_versions(model_id, created_at DESC);

CREATE INDEX idx_model_versions_dataset_version
    ON model_versions(dataset_version_id);


-- 모델당 PRODUCTION 버전은 최대 하나
CREATE UNIQUE INDEX uq_model_versions_production_per_model
    ON model_versions(model_id)
    WHERE deployment_status = 'PRODUCTION';


-- training_job_model_versions
CREATE INDEX idx_training_job_model_versions_model_version_id
    ON training_job_model_versions(model_version_id);


-- training_attempts
CREATE INDEX idx_training_attempts_status_started_at
    ON training_attempts(status, started_at);

CREATE INDEX idx_training_attempts_training_job_id
    ON training_attempts(training_job_id);