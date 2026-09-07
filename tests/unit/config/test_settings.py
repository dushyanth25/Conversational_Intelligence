import pytest
from pydantic import ValidationError

from config.settings import Settings, get_settings


def test_default_values():
    """Test that default values are correctly populated."""
    settings = Settings()

    assert settings.APP_ENV == "development"
    assert settings.PARAMETERS_PER_BATCH == 3
    assert settings.PARALLEL_WORKERS == 1
    assert settings.AUDIO_SAMPLE_RATE == 16000
    assert settings.AUDIO_CHANNELS == 1
    assert settings.VAD_ENABLED is True
    assert settings.VAD_MODEL == "silero_vad"
    assert settings.ASR_DEVICE == "cpu"
    assert settings.DIARIZATION_DEVICE == "cpu"


def test_environment_overrides(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PARAMETERS_PER_BATCH", "5")
    monkeypatch.setenv("ASR_DEVICE", "cuda")

    settings = Settings()

    assert settings.APP_ENV == "production"
    assert settings.PARAMETERS_PER_BATCH == 5
    assert settings.ASR_DEVICE == "cuda"


def test_invalid_batch_size(monkeypatch):
    """Test that an invalid batch size (e.g., 0) raises a validation error."""
    monkeypatch.setenv("PARAMETERS_PER_BATCH", "0")
    with pytest.raises(ValidationError):
        Settings()

    monkeypatch.setenv("PARAMETERS_PER_BATCH", "-1")
    with pytest.raises(ValidationError):
        Settings()


def test_invalid_worker_count(monkeypatch):
    """Test that an invalid worker count raises a validation error."""
    monkeypatch.setenv("PARALLEL_WORKERS", "0")
    with pytest.raises(ValidationError):
        Settings()


def test_valid_environments(monkeypatch):
    """Test valid environment variations."""
    monkeypatch.setenv("APP_ENV", "development")
    settings = Settings()
    assert settings.APP_ENV == "development"

    monkeypatch.setenv("APP_ENV", "production")
    settings = Settings()
    assert settings.APP_ENV == "production"

    monkeypatch.setenv("APP_ENV", "testing")
    settings = Settings()
    assert settings.APP_ENV == "testing"


def test_invalid_environment(monkeypatch):
    """Test that an invalid environment raises a validation error."""
    monkeypatch.setenv("APP_ENV", "invalid_env")
    with pytest.raises(ValidationError):
        Settings()


def test_invalid_device(monkeypatch):
    """Test that an invalid device raises a validation error."""
    monkeypatch.setenv("ASR_DEVICE", "tpu")
    with pytest.raises(ValidationError):
        Settings()


def test_missing_required_secrets(monkeypatch):
    """Test how the settings system handles secrets.
    Here we expect them to be optional or loaded securely."""
    # Since we set them as Optional[SecretStr], they should be None by default
    settings = Settings(_env_file=None)
    assert settings.GROQ_API_KEY is None
    assert settings.POSTGRES_PASSWORD is None
    assert settings.MINIO_SECRET_KEY is None


def test_secrets_are_not_exposed_in_repr(monkeypatch):
    """Test that secrets are wrapped in SecretStr and not exposed."""
    monkeypatch.setenv("GROQ_API_KEY", "super_secret_groq_key")
    monkeypatch.setenv("POSTGRES_PASSWORD", "super_secret_db_pass")

    settings = Settings()

    repr_string = repr(settings)
    assert "super_secret_groq_key" not in repr_string
    assert "super_secret_db_pass" not in repr_string

    # Prove that the value is still accessible when needed
    assert settings.GROQ_API_KEY.get_secret_value() == "super_secret_groq_key"


def test_get_settings_caching():
    """Test that get_settings() returns a cached instance."""
    settings_1 = get_settings()
    settings_2 = get_settings()
    assert settings_1 is settings_2
