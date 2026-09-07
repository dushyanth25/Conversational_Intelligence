import importlib
from pathlib import Path

import pytest


def test_project_directories_exist():
    """Verify that the required project directories exist."""
    base_dir = Path(__file__).parent.parent.parent

    required_dirs = [
        "api",
        "api/routes",
        "api/schemas",
        "api/services",
        "pipeline",
        "pipeline/preprocessing",
        "pipeline/vad",
        "pipeline/transcription",
        "pipeline/diarization",
        "pipeline/alignment",
        "pipeline/speaker_tagging",
        "pipeline/transcript",
        "pipeline/insights",
        "pipeline/aggregation",
        "pipeline/validation",
        "llm",
        "storage",
        "storage/postgres",
        "storage/minio",
        "workflows",
        "workflows/argo",
        "models",
        "config",
        "common",
        "common/exceptions",
        "common/logging",
        "common/utilities",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "scripts",
        "Dockerfiles",
        "requirements",
    ]

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        assert full_path.exists() and full_path.is_dir(), (
            f"Directory missing: {dir_path}"
        )


def test_python_packages_importable():
    """Verify that main python packages can be imported."""
    packages = [
        "api",
        "pipeline",
        "llm",
        "storage",
        "workflows",
        "models",
        "config",
        "common",
    ]

    for package in packages:
        try:
            importlib.import_module(package)
        except ImportError as e:
            pytest.fail(f"Could not import package {package}: {e}")
