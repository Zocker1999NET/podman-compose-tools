from typing import Iterable, List, NewType, Optional


CommandArgs = NewType("CommandArgs", List[str])
ShellCommandStr = NewType("ShellCommandStr", str)


def filter_cmds(command: Iterable[Optional[str]]) -> CommandArgs:
    return CommandArgs([arg for arg in command if arg is not None])


def combine_cmds(*commands: CommandArgs | List[Optional[str]]) -> CommandArgs:
    return CommandArgs([arg for cmd in commands for arg in filter_cmds(cmd)])
