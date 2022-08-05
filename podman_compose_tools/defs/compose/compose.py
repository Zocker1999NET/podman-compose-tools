from __future__ import annotations

from pathlib import Path
from typing import Mapping, NewType, Optional, TypedDict

from .service import ServiceName, ServiceDef
from .volume import VolumeName, VolumeDef


ComposeVersion = NewType("ComposeVersion", str)


class _ComposeDefRequired(TypedDict):
    _dirname: Path
    version: ComposeVersion


class ComposeDef(_ComposeDefRequired, total=False):
    services: Mapping[ServiceName, ServiceDef]
    volumes: Mapping[VolumeName, Optional[VolumeDef]]
