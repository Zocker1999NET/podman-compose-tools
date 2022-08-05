from __future__ import annotations

from typing import Any, Type, TypeVar


T = TypeVar("T", bound="Singleton")


class Singleton(type):
    _instances = dict[Type, Any]()

    def __call__(cls: T, *args, **kwargs) -> T:
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


__all__ = ["Singleton"]
