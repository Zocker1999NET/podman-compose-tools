from __future__ import annotations

import abc
from pathlib import PurePath
import shlex
from typing import Callable, Iterable, List, Optional

from attrs import define

from .base import CommandArgs, ShellCommandStr
from .completed import CompletedExec
from .execution import ExecutorTarget


class Command(metaclass=abc.ABCMeta):
    def __call__(
        self,
        executor: ExecutorTarget,
        check: bool = True,
        capture_stdout: bool = True,
    ) -> CompletedExec:
        return self.run(
            executor=executor,
            check=check,
            capture_stdout=capture_stdout,
        )

    @abc.abstractmethod
    def run(
        self,
        *,
        executor: ExecutorTarget,
        check: bool = True,
        capture_stdout: bool = True,
    ) -> CompletedExec:
        ...


@define
class ArgCommand(Command):
    args: List[str]

    @classmethod
    def from_single(cls, arg: str) -> ArgCommand:
        return cls(args=[arg])

    def __add__(
        self,
        other: ArgCommand | CommandArgs | Iterable[Optional[str]],
    ) -> ArgCommand:
        if isinstance(other, ArgCommand):
            return ArgCommand(args=self.args + other.args)
        return ArgCommand(args=self.args + [arg for arg in other if arg is not None])

    def __radd__(
        self,
        other: ArgCommand | CommandArgs | Iterable[Optional[str]],
    ) -> ArgCommand:
        if isinstance(other, ArgCommand):
            return ArgCommand(args=other.args + self.args)
        return ArgCommand(args=[arg for arg in other if arg is not None] + self.args)

    def __and__(
        self,
        other: Optional[str],
    ) -> ArgCommand:
        if other is None:
            return self
        return self + [other]

    def __str__(self) -> str:
        return " ".join(shlex.quote(arg) for arg in self.args)

    def to_shell_cmd(self) -> ShellCommand:
        return ShellCommand(command=str(self))

    def run(
        self,
        *,
        executor: ExecutorTarget,
        check: bool = True,
        capture_stdout: bool = True,
        work_dir: Optional[PurePath] = None,
    ) -> CompletedExec:
        return executor.exec_cmd(
            command=CommandArgs(self.args),
            check=check,
            capture_stdout=capture_stdout,
            work_dir=work_dir,
        )


@define(order=False)
class ShellCommand(Command):
    command: str

    @staticmethod
    def _extract_other(
        method: Callable[[ShellCommand, str], str]
    ) -> Callable[[ShellCommand, Command], ShellCommand]:
        def decorated(self, other: Command) -> ShellCommand:
            other_cmd: str
            if isinstance(other, Command):
                other_cmd = str(other)
            else:
                return NotImplemented
            return ShellCommand(method(self, other_cmd))

        return decorated

    @staticmethod
    def _parse_path(
        method: Callable[[ShellCommand, str], str]
    ) -> Callable[[ShellCommand, PurePath | str], ShellCommand]:
        def decorated(self, other: PurePath | str) -> ShellCommand:
            other_cmd: str
            if isinstance(other, str):
                other_cmd = other
            elif isinstance(other, PurePath):
                other_cmd = str(other)
            else:
                return NotImplemented
            return ShellCommand(method(self, other_cmd))

        return decorated

    @classmethod
    def from_str(cls, command: str) -> ShellCommand:
        return cls(
            command=command,
        )

    @_extract_other
    def __or__(self, other_cmd: str) -> str:  # |
        return f"({self.command}) | ({other_cmd})"

    @_extract_other
    def __ror__(self, other_cmd: str) -> str:  # |
        return f"({other_cmd}) | ({self.command})"

    @_parse_path
    def __lt__(self, other: str) -> str:  # <
        return f"{self.command} < {shlex.quote(other)}"

    @_parse_path
    def __gt__(self, other: str) -> str:  # >
        return f"{self.command} > {shlex.quote(other)}"

    def __str__(self) -> str:
        return self.command

    def run(
        self,
        *,
        executor: ExecutorTarget,
        check: bool = True,
        capture_stdout: bool = True,
        work_dir: Optional[PurePath] = None,
    ) -> CompletedExec:
        return executor.exec_shell(
            shell_cmd=ShellCommandStr(self.command),
            check=check,
            capture_stdout=capture_stdout,
            work_dir=work_dir,
        )
