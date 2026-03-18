from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from codessa_memory.api.app_factory import create_app
from codessa_memory.di.container import Container, Lifetime
from codessa_memory.utils.config import Settings


class A:
    def __init__(self) -> None:
        self.value = object()


class B:
    def __init__(self, a: A) -> None:
        self.a = a


def test_container_singleton_reuses_instance() -> None:
    c = Container()
    c.register(A, lambda _c, _s: A(), lifetime=Lifetime.SINGLETON)
    assert c.resolve(A) is c.resolve(A)


def test_container_transient_creates_new_instance() -> None:
    c = Container()
    c.register(A, lambda _c, _s: A(), lifetime=Lifetime.TRANSIENT)
    assert c.resolve(A) is not c.resolve(A)


def test_container_scoped_reuses_within_scope_and_not_across_scopes() -> None:
    c = Container()
    c.register(A, lambda _c, _s: A(), lifetime=Lifetime.SCOPED)
    s1: dict[type[object], object] = {}
    s2: dict[type[object], object] = {}
    assert c.resolve(A, scope=s1) is c.resolve(A, scope=s1)
    assert c.resolve(A, scope=s1) is not c.resolve(A, scope=s2)


def test_container_validate_fails_on_missing_dependency() -> None:
    c = Container()

    def _b(container: Container, scope) -> B:
        return B(container.resolve(A, scope=scope))

    c.register(B, _b, lifetime=Lifetime.SINGLETON)
    with pytest.raises(KeyError):
        c.validate()


def test_app_builds_and_health_is_ok(tmp_path) -> None:
    app_settings = Settings(app_env="test", app_name="codessa-memory-test", local_data_dir=str(tmp_path))
    client = TestClient(create_app(app_settings=app_settings))
    res = client.get("/health")
    assert res.status_code == 200
