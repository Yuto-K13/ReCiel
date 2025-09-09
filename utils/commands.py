import inspect
from collections.abc import Generator, Sequence
from typing import overload

from discord import Interaction
from discord.app_commands import AppCommand, AppCommandError, AppCommandGroup, Argument, Command, ContextMenu, Group


async def check_can_run(command: Command | ContextMenu, interaction: Interaction) -> bool:
    for check in command.checks:
        try:
            result = check(interaction)
            if inspect.isawaitable(result):
                result = await result
        except AppCommandError:
            return False
        if not result:
            return False
    return True


@overload
def expand_commands(commands: list[Command | Group]) -> Generator[Command]: ...
@overload
def expand_commands(commands: list[Command | Group | ContextMenu]) -> Generator[Command | ContextMenu]: ...
@overload
def expand_commands(commands: list[AppCommand]) -> Generator[AppCommand | AppCommandGroup]: ...


def expand_commands(
    commands: list[Command | Group] | list[Command | Group | ContextMenu] | list[AppCommand],
) -> Generator[Command | ContextMenu | AppCommand | AppCommandGroup]:
    cmds: Sequence[Command | Group | ContextMenu | AppCommand | AppCommandGroup | Argument] = commands.copy()
    while cmds:
        cmd = cmds.pop(0)
        if isinstance(cmd, Group):
            cmds = cmd.commands + cmds
            continue
        if isinstance(cmd, (AppCommand, AppCommandGroup)):
            cmds = cmd.options + cmds
            continue
        if isinstance(cmd, Argument):
            continue
        yield cmd
