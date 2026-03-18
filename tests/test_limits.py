from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from codessa_memory.api.app_factory import create_app
from codessa_memory.limits.service import RateLimiter
from codessa_memory.utils.config import Settings


def test_rate_limiter_allows_until_limit_and_then_blocks() -> None:
    limiter = RateLimiter(requests_per_minute=2)
    assert limiter.check("u1", now=0.0) == (True, 0)
    assert limiter.check("u1", now=0.1) == (True, 0)
    allowed, retry_after = limiter.check("u1", now=0.2)
    assert allowed is False
    assert retry_after >= 1


def test_rate_limiter_resets_on_next_window() -> None:
    limiter = RateLimiter(requests_per_minute=1)
    assert limiter.check("u1", now=10.0) == (True, 0)
    assert limiter.check("u1", now=20.0)[0] is False
    assert limiter.check("u1", now=70.0) == (True, 0)


def test_rate_limiter_separates_keys() -> None:
    limiter = RateLimiter(requests_per_minute=1)
    assert limiter.check("u1", now=0.0) == (True, 0)
    assert limiter.check("u2", now=0.0) == (True, 0)
    assert limiter.check("u1", now=1.0)[0] is False


def test_rate_limiter_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError):
        RateLimiter(requests_per_minute=0)


def test_rate_limit_middleware_enforces_429(tmp_path) -> None:
    app_settings = Settings(
        app_env="test",
        app_name="codessa-memory-test",
        local_data_dir=str(tmp_path),
        default_chunk_size=50,
        default_chunk_overlap=0,
        top_k=2,
        rate_limit_enabled=True,
        rate_limit_requests_per_minute=2,
    )
    client = TestClient(create_app(app_settings=app_settings))

    for _ in range(2):
        res = client.post("/query", json={"query": "hello"})
        assert res.status_code == 200

    res = client.post("/query", json={"query": "hello"})
    assert res.status_code == 429
    assert int(res.headers["Retry-After"]) >= 1


def test_health_is_not_rate_limited(tmp_path) -> None:
    app_settings = Settings(
        app_env="test",
        app_name="codessa-memory-test",
        local_data_dir=str(tmp_path),
        rate_limit_enabled=True,
        rate_limit_requests_per_minute=1,
    )
    client = TestClient(create_app(app_settings=app_settings))
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
