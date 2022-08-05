from __future__ import annotations

from pathlib import PurePath
from typing import Optional

from attrs import define

from .base import CommandArgs
from .command import ArgCommand
from .completed import CompletedExec
from .execution import ExecutorTarget


@define
class BinaryExecutor(ExecutorTarget):
    binary_args: CommandArgs

    def exec_cmd(
        self,
        *,
        command: CommandArgs,
        check: bool,
        capture_stdout: bool,
        work_dir: Optional[PurePath],
    ) -> CompletedExec:
        return super().exec_cmd(
            command=CommandArgs(self.binary_args + command),
            check=check,
            capture_stdout=capture_stdout,
            work_dir=work_dir,
        )
