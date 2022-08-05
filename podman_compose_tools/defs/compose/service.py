from __future__ import annotations

from typing import Literal, NewType, Sequence, TypeAlias, TypedDict


ServiceName = NewType("ServiceName", str)
ContainerName = NewType("ContainerName", str)


class ServiceDef(TypedDict, total=False):
    container_name: ContainerName
    depends_on: Sequence[ServiceName]
