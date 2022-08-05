from __future__ import annotations

from typing import NewType, TypedDict


VolumeName = NewType("VolumeName", str)
PublicVolumeName = NewType("PublicVolumeName", str)


class VolumeDef(TypedDict, total=False):
    name: PublicVolumeName
