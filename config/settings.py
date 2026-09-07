from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, PositiveFloat, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "conversation-intelligence"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # Audio
    SUPPORTED_AUDIO_FORMATS: str = "wav,mp3,m4a,flac"
    AUDIO_SAMPLE_RATE: PositiveInt = 16000
    AUDIO_CHANNELS: PositiveInt = 1

    # VAD
    VAD_ENABLED: bool = True
    VAD_MODEL: str = "silero_vad"

    # ASR
    ASR_MODEL: str = "base"
    ASR_DEVICE: Literal["cpu", "cuda"] = "cpu"
    ASR_COMPUTE_TYPE: str = "int8"
    ASR_LANGUAGE: str = "en"
    ASR_MODEL_CACHE_DIR: Optional[str] = None

    # Diarization
    DIARIZATION_ENABLED: bool = True
    DIARIZATION_MODEL: str = "pyannote/speaker-diarization-3.0"
    DIARIZATION_DEVICE: Literal["cpu", "cuda"] = "cpu"
    DIARIZATION_MODEL_CACHE_DIR: Optional[str] = None
    HF_TOKEN: Optional[SecretStr] = None

    # Insight Processing
    PARAMETERS_PER_BATCH: PositiveInt = 3
    PARALLEL_WORKERS: PositiveInt = 1

    # Groq
    GROQ_API_KEY: Optional[SecretStr] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=2.0)
    GROQ_MAX_TOKENS: PositiveInt = 1024
    GROQ_TIMEOUT: PositiveFloat = 30.0
    GROQ_MAX_RETRIES: int = Field(default=3, ge=0)
    GROQ_RETRY_BACKOFF: PositiveFloat = 2.0
    MAX_TRANSCRIPT_LENGTH: PositiveInt = 100000

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: PositiveInt = 5432
    POSTGRES_DB: str = "conversational_intelligence"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: Optional[SecretStr] = None

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: Optional[SecretStr] = None
    MINIO_BUCKET: str = "conversation-intelligence"
    MINIO_SECURE: bool = False

    # Storage prefixes
    RAW_AUDIO_PREFIX: str = "raw/"
    PROCESSED_AUDIO_PREFIX: str = "processed/"
    TRANSCRIPT_PREFIX: str = "transcripts/"
    DIARIZED_PREFIX: str = "diarized/"
    INSIGHTS_PREFIX: str = "insights/"

    # Argo
    ARGO_SERVER: str = "http://localhost:2746"
    ARGO_NAMESPACE: str = "default"
    ARGO_WORKFLOW_TEMPLATE: str = "conversation-pipeline-template"
    ARGO_TOKEN: Optional[SecretStr] = None
    
    # API
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"

    # Databricks
    DATABRICKS_HOST: Optional[str] = None
    DATABRICKS_HTTP_PATH: Optional[str] = None
    DATABRICKS_TOKEN: Optional[SecretStr] = None
    DATABRICKS_CATALOG: str = "main"
    DATABRICKS_SCHEMA: str = "default"
    DATABRICKS_TABLE: str = "conversations"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the settings."""
    return Settings()
