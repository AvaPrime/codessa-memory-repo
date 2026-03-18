from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class Lifetime(str, Enum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


Scope = dict[type[Any], Any]
Factory = Callable[["Container", Scope], Any]


@dataclass(frozen=True)
class Registration:
    factory: Factory
    lifetime: Lifetime


class Container:
    def __init__(self) -> None:
        self._registrations: dict[type[Any], Registration] = {}
        self._singletons: dict[type[Any], Any] = {}

    def register(
        self,
        key: type[T],
        factory: Callable[["Container", Scope], T],
        lifetime: Lifetime = Lifetime.SINGLETON,
    ) -> None:
        self._registrations[key] = Registration(factory=factory, lifetime=lifetime)

    def register_instance(self, key: type[T], instance: T) -> None:
        self._registrations[key] = Registration(factory=lambda _c, _s: instance, lifetime=Lifetime.SINGLETON)
        self._singletons[key] = instance

    def resolve(self, key: type[T], scope: Scope | None = None) -> T:
        registration = self._registrations.get(key)
        if registration is None:
            raise KeyError(f"Service not registered: {key.__name__}")

        if registration.lifetime == Lifetime.SINGLETON:
            if key in self._singletons:
                return self._singletons[key]
            instance = registration.factory(self, {})
            self._singletons[key] = instance
            return instance

        if registration.lifetime == Lifetime.SCOPED:
            if scope is None:
                raise RuntimeError("Scoped resolution requires a scope")
            if key in scope:
                return scope[key]
            instance = registration.factory(self, scope)
            scope[key] = instance
            return instance

        return registration.factory(self, scope or {})

    def validate(self, keys: Iterable[type[Any]] | None = None) -> None:
        to_validate = list(keys) if keys is not None else list(self._registrations.keys())
        for key in to_validate:
            self.resolve(key, scope={})

    def apply_overrides(self, overrides: Mapping[type[Any], Any]) -> None:
        for key, value in overrides.items():
            if callable(value):
                self.register(key, value, lifetime=Lifetime.SINGLETON)
            else:
                self.register_instance(key, value)
