from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from codessa_memory.api.app_factory import create_app
from codessa_memory.utils.config import Settings


@pytest.fixture()
def app_settings(tmp_path) -> Settings:
    return Settings(
        app_env="test",
        app_name="codessa-memory-test",
        storage_backend="local",
        local_data_dir=str(tmp_path),
        default_chunk_size=100,
        default_chunk_overlap=10,
        top_k=3,
    )


@pytest.fixture()
def client(app_settings: Settings) -> TestClient:
    app = create_app(app_settings=app_settings)
    return TestClient(app)
