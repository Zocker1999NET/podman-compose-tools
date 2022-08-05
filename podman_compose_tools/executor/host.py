from __future__ import annotations

from pathlib import PurePath
import subprocess
from typing import Optional

from .base import CommandArgs
from .completed import CompletedExec
from .execution import ExecutorTarget
from ..misc.singleton import Singleton


class HostExecutor(ExecutorTarget, metaclass=Singleton):
    def exec_cmd(
        self,
        *,
        command: CommandArgs,
        check: bool,
        capture_stdout: bool,
        work_dir: Optional[PurePath] = None,
    ) -> CompletedExec:
        return CompletedExec(
            subprocess.run(
                args=command,
                check=check,
                cwd=work_dir,
                shell=False,
                stdout=subprocess.PIPE if capture_stdout else None,
            )
        )
