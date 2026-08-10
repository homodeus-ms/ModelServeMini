from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str
    dataset_storage_path: str = "storage/datasets"
    model_storage_path: str = "storage/models"

    kafka_bootstrap_servers: str = "localhost:9092"

    redis_host: str = "localhost"
    redis_port: int = 6379

    gpu_scheduler_url: str = "http://localhost:8010"

settings = Settings()