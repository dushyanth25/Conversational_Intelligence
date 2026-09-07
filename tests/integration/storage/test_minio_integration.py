import os

import pytest


@pytest.mark.skipif(
    not os.environ.get("MINIO_INTEGRATION_TEST"), 
    reason="MinIO integration tests require a running MinIO server"
)
def test_minio_integration():
    """
    Optional integration test against a local MinIO instance.
    To run this test, ensure MinIO is running and set MINIO_INTEGRATION_TEST=1.
    """
    pass
