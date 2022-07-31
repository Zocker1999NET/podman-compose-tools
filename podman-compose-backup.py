#!/usr/bin/env python3


# TODO implement backup single vol
# TODO implement restore single vol
# TODO decide upon depends_on and volume mounts which containers must be shut down and which turned on for single volume backup (def)
# TODO group decision for multiple/all volumes (at first, throw error if incompatible as backed up state might be inconsistent)
# TODO store full backup (= all volumes) inside one (uncompressed) tar archive
# TODO support env-files
# TODO throw error/hint on bind mounts (not supported for now)

# TODO test with normal volume
# TODO test with mariadb
# TODO test with entertainment-decider (testing depends_on)
# TODO test with small nextcloud instance

# TODO append compose and referenced files into tar for easy migration
# TODO add support for restoring from easy migration tar archive
# TODO add profile support (if applicable), e.g. mysql/mariadb


# === imports


from __future__ import annotations
import argparse

from functools import cached_property, wraps
import os
from pathlib import Path
import shlex
import sys
from typing import (
    Dict,
    Iterable,
    List,
    Mapping,
    NewType,
    Optional,
    Sequence,
    TypeAlias,
    TypedDict,
)

from attrs import define, field
from podman_compose import normalize, rec_merge, rec_subs
import yaml


# === custom types


ProjectName = NewType("ProjectName", str)
ShellCommand = NewType("ShellCommand", str)
CommandArgs = NewType("CommandArgs", List[Optional[str]])

ComposeVersion = NewType("ComposeVersion", str)
ContainerName = NewType("ContainerName", str)
PublicVolumeName = NewType("PublicVolumeName", str)

ServiceName = NewType("ServiceName", str)
VolumeName = NewType("VolumeName", str)

LabelDict: TypeAlias = Mapping[str, str]


class _ComposeDefRequired(TypedDict):
    _dirname: Path
    version: ComposeVersion


class ComposeDef(_ComposeDefRequired, total=False):
    services: Mapping[ServiceName, ComposeServiceDef]
    volumes: Mapping[VolumeName, Optional[ComposeVolumeDef]]


class ComposeServiceDef(TypedDict, total=False):
    container_name: ContainerName
    depends_on: Sequence[ServiceName]


class ComposeVolumeDef(TypedDict, total=False):
    name: PublicVolumeName


# === constants


# multiple prefixes for adding more if project becomes standardized
# first label takes precendence
LABEL_PREFIXES = [
    "work.banananet.podman.backup.",
]

DEFAULT_MOUNT_TARGET = "/_volume"
DEFAULT_BACKUP_IMAGE = "docker.io/library/debian:stable"
DEFAULT_BACKUP_CMD = "tar -cf - ."
DEFAULT_RESTORE_CMD = "tar -xf -"


# List of POSIX shells which shall be used
DETECTED_SHELLS = [
    "/usr/bin/bash",
    "/bin/bash",
    "/usr/bin/sh",
    "/bin/sh",
]

PODMAN_EXEC = CommandArgs(
    [
        "/usr/bin/env",
        "podman",
    ]
)
PODMAN_COMPOSE_EXEC = CommandArgs(
    [
        "/usr/bin/env",
        "podman-compose",
    ]
)


# === helpers


def filter_cmds(command: Iterable[Optional[str]]) -> CommandArgs:
    return CommandArgs([arg for arg in command if arg is not None])


def combine_cmds(*commands: CommandArgs | List[Optional[str]]) -> CommandArgs:
    return CommandArgs([arg for cmd in commands for arg in filter_cmds(cmd)])


@wraps(print)
def error(*args, **kwargs):
    ret = print(*args, file=sys.stderr, **kwargs)
    sys.stderr.flush()
    return ret


def parse_bool(val: str | bool) -> bool:
    if isinstance(val, bool):
        return val
    return val.lower().startswith(("t", "y", "1"))


# === code


@define(kw_only=True)
class VolumeBackupConfig:
    # === Backups
    enable: bool = field(converter=parse_bool, default=True)
    container: Optional[str] = field(default=None)
    image: str = field(default=DEFAULT_BACKUP_IMAGE)
    mount_target: str = field(default=DEFAULT_MOUNT_TARGET)
    stop: bool = field(converter=parse_bool, default=False)
    backup_cmd: str = field(default=DEFAULT_BACKUP_CMD)
    restore_cmd: str = field(default=DEFAULT_RESTORE_CMD)
    # === Compressing
    compress_image: Optional[str] = field(default=None)
    compress_cmd: Optional[str] = field(default=None)
    decompress_cmd: Optional[str] = field(default=None)

    @classmethod
    def from_labels(cls, labels: LabelDict) -> VolumeBackupConfig:
        return cls(**parse_labels(labels=labels))

    def __attrs_post_init__(self):
        if self.compress_cmd is None:
            if self.decompress_cmd is not None:
                # TODO specialize
                raise Exception(
                    "compress-cmd must be specified as it cannot be retrieved from decompress-cmd"
                )
        else:
            self.decompress_cmd = f"{self.compress_cmd} -d"


class ComposeFile:

    project_name: ProjectName
    environ: Dict[str, str]
    compose: ComposeDef
    compose_files: Sequence[Path]

    def __init__(
        self,
        *compose_files: Path,
        project_name: Optional[ProjectName] = None,
    ):
        self.compose_files = compose_files
        ref_dir = compose_files[0].parent
        self.project_name = project_name or ProjectName(ref_dir.name)
        compose: ComposeDef = {
            "_dirname": ref_dir,
            "version": ComposeVersion("0"),
        }
        self.environ = dict(os.environ)
        for path in compose_files:
            with open(path, "r") as fh:
                content = yaml.safe_load(fh)
                if not isinstance(content, dict):
                    error(f"Compose file does not contain a top level object: {path}")
                    sys.exit(1)
                content = normalize(content)
                content = rec_subs(content, self.environ)
                rec_merge(compose, content)
        self.compose = compose
        if not self.version.startswith("3."):
            error(
                f"Compose file version is not supported, only support 3.X compose files"
            )
            sys.exit(1)

    @property
    def version(self) -> ComposeVersion:
        return self.compose.get("version", ComposeVersion(""))

    @property
    def __services_defs(self) -> Mapping[ServiceName, ComposeServiceDef]:
        return self.compose.get("services", {})

    @property
    def __volumes_defs(self) -> Mapping[VolumeName, Optional[ComposeVolumeDef]]:
        return self.compose.get("volumes", {})

    @cached_property
    def services(self) -> Mapping[ServiceName, ComposeContainer]:
        return {
            name: ComposeContainer(compose=self, name=name, base=opts or {})
            for name, opts in self.__services_defs.items()
        }

    @cached_property
    def volumes(self) -> Mapping[VolumeName, ComposeVolume]:
        return {
            name: ComposeVolume(compose=self, name=name, base=opts or {})
            for name, opts in self.__volumes_defs.items()
        }

    @property
    def compose_cmd(self) -> CommandArgs:
        return CommandArgs(
            PODMAN_COMPOSE_EXEC
            + [f"--project-name=self.project_name"]
            + [f"--file={file}" for file in self.compose_files]
        )


@define(kw_only=True)
class ComposeContainer:

    compose: ComposeFile
    name: ServiceName
    base: ComposeServiceDef

    @property
    def container_name(self) -> ContainerName:
        return self.base.get(
            "container_name",
            ContainerName(f"{self.compose.project_name}_{self.name}_1"),
        )

    @cached_property
    def depends_on(self) -> Sequence[ComposeContainer]:
        return [self.compose.services[name] for name in self.base.get("depends_on", [])]

    def exec_cmd(
        self, command: CommandArgs, workdir: Optional[str] = None
    ) -> CommandArgs:
        return CommandArgs(
            PODMAN_EXEC
            + [
                "container",
                "exec",
                "--interactive=false",
                None if workdir is None else f"--workdir={workdir}",
                self.container_name,
            ]
            + command
        )


@define(kw_only=True)
class ComposeVolume:

    compose: ComposeFile
    name: VolumeName
    base: ComposeVolumeDef

    @cached_property
    def public_name(self) -> PublicVolumeName:
        return self.base.get(
            "name", PublicVolumeName(f"{self.compose.project_name}_{self.name}")
        )


def parse_labels(labels: LabelDict) -> LabelDict:
    ret = dict[str, str]()
    for key, val in labels.items():
        for prefix in LABEL_PREFIXES:
            if key.startswith(prefix):
                new_key = key.removeprefix(prefix).replace("-", "_")
                ret[new_key] = val
                break
    return ret


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="podman-compose-backup",
        description="Backups & restores compose volumes according to their configuration",
    )
    parser.add_argument(
        "-f",
        "--file",
        nargs="*",
        type=Path,
        default=(Path("./docker-compose.yml"),),
        help="Specify an alternate compose file (default: docker-compose.yml)",
    )
    parser.add_argument(
        "-p",
        "--project-name",
        type=ProjectName,
        default=None,
        help="Specify an alternate project name (default: directory name)",
    )
    return parser.parse_args(args=args)


def exec(given_args: Sequence[str]):
    args = parse_args(args=given_args)
    compose = ComposeFile(*args.file, project_name=args.project_name)
    print(compose.compose_cmd)


def cli(args: Sequence[str]):
    try:
        exec(given_args=args)
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as e:
        error(f"{e.strerror}: {e.filename}")
        sys.exit(2)


if __name__ == "__main__":
    cli(sys.argv[1:])
