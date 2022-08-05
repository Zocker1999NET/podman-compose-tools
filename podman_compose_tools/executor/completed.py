import json
from subprocess import CompletedProcess
from typing import Any, Mapping

from attrs import define


@define()
class CompletedExec:
    completed_process: CompletedProcess

    @property
    def returncode(self) -> int:
        return self.completed_process.returncode

    def check_returncode(self) -> None:
        return self.completed_process.check_returncode()

    def to_json(self) -> Mapping[str, Any]:
        return json.loads(self.completed_process.stdout)
