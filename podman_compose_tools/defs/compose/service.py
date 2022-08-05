from __future__ import annotations

from typing import Literal, NewType, Sequence, TypeAlias, TypedDict

from .volume import VolumeName


ServiceName = NewType("ServiceName", str)
ContainerName = NewType("ContainerName", str)


class ServiceDef(TypedDict, total=False):
    container_name: ContainerName
    depends_on: Sequence[ServiceName]
    volumes: Sequence[VolumeDef]


# === Service Volumes


_VolumeShort = NewType("_VolumeShort", str)
"format: [SOURCE:]TARGET[:MODE] where MODE is either rw or ro"


class _VolumeGeneral(TypedDict, total=False):
    read_only: bool


# volume type: volume


class _VolumeNaturalConfig(TypedDict, total=False):
    nocopy: bool


class _VolumeNaturalRequired(TypedDict, total=True):
    type: Literal["volume"]
    source: VolumeName
    target: str


class _VolumeNatural(_VolumeNaturalRequired, _VolumeGeneral, total=False):
    volume: _VolumeNaturalConfig


# volume type: bind


class _VolumeBindConfig(TypedDict, total=False):
    propagation: str


class _VolumeBindRequired(TypedDict, total=True):
    type: Literal["bind"]
    source: str
    target: str


class _VolumeBind(_VolumeBindRequired, _VolumeGeneral, total=False):
    volume: _VolumeBindConfig


# volume type: tmpfs


class _VolumeTmpfsConfig(TypedDict, total=False):
    size: int
    "in bytes"


class _VolumeTmpfsRequired(TypedDict, total=True):
    type: Literal["tmpfs"]
    target: str


class _VolumeTmpfs(_VolumeTmpfsRequired, _VolumeGeneral, total=False):
    tmpfs: _VolumeTmpfsConfig


# volume type: npipe


class _VolumeNpipeRequired(TypedDict, total=True):
    type: Literal["npipe"]
    target: str


class _VolumeNpipe(_VolumeNpipeRequired, _VolumeGeneral, total=False):
    pass


# end volume types


_VolumeLong: TypeAlias = _VolumeNatural | _VolumeBind | _VolumeTmpfs | _VolumeNpipe

VolumeDef: TypeAlias = _VolumeShort | _VolumeLong
