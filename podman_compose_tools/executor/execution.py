import abc
from functools import cached_property
from pathlib import PurePath
from typing import Callable, Optional

from attrs import define

from .base import CommandArgs, ShellCommandStr
from .completed import CompletedExec


# List of POSIX shells which shall be used
DETECTED_SHELLS = [
    "/usr/bin/bash",
    "/bin/bash",
    "/usr/bin/sh",
    "/bin/sh",
]


class ExecutorTarget(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def exec_cmd(
        self,
        *,
        command: CommandArgs,
        check: bool,
        capture_stdout: bool,
        work_dir: Optional[PurePath],
    ) -> CompletedExec:
        ...

    @staticmethod
    def process_tester(
        exec: Callable[[CommandArgs], CompletedExec]
    ) -> Callable[[CommandArgs], bool]:
        return lambda command: exec(command).returncode == 0

    @staticmethod
    def _search_shell_with(tester: Callable[[CommandArgs], bool]) -> str:
        for shell in DETECTED_SHELLS:
            command = CommandArgs([shell, "-c", "true"])
            if tester(command):
                return command[0]
        # TODO specialize
        raise Exception(
            f"Could not find an acceptable shell on this host, searched for {DETECTED_SHELLS}"
        )

    @cached_property
    def found_shell(self) -> str:
        return self._search_shell_with(
            self.process_tester(
                lambda command: self.exec_cmd(
                    command=command,
                    check=False,
                    capture_stdout=False,
                    work_dir=None,
                )
            )
        )

    def exec_shell(
        self,
        *,
        shell_cmd: ShellCommandStr,
        check: bool,
        capture_stdout: bool,
        work_dir: Optional[PurePath],
    ) -> CompletedExec:
        return self.exec_cmd(
            command=CommandArgs([self.found_shell, "-c", shell_cmd]),
            check=check,
            capture_stdout=capture_stdout,
            work_dir=work_dir,
        )
