import inspect
from collections.abc import Generator, Sequence
from typing import overload

from discord import DMChannel, Interaction
from discord.abc import GuildChannel, PrivateChannel
from discord.app_commands import AppCommand, AppCommandError, AppCommandGroup, Argument, Command, ContextMenu, Group

from .types import CielType


def _is_command_available_channel(command: Command | ContextMenu, interaction: Interaction) -> bool:
    client: CielType = interaction.client  # pyright: ignore[reportAssignmentType]
    if client:
        guild = interaction.guild
        runnable = set()
        runnable.update(expand_commands(client.tree.get_commands(guild=None)))
        runnable.update(expand_commands(client.tree.get_commands(guild=guild)))
        if command not in runnable:
            return False

    contexts = command.allowed_contexts
    if contexts:
        channel = interaction.channel
        if (
            not (isinstance(channel, GuildChannel) and contexts.guild)
            and not (isinstance(channel, DMChannel) and contexts.dm_channel)
            and not (isinstance(channel, PrivateChannel) and contexts.private_channel)
        ):
            return False
    return True


async def _is_command_checks_passed(command: Command | ContextMenu, interaction: Interaction) -> bool:
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


async def can_run_command(command: Command | ContextMenu, interaction: Interaction) -> bool:
    if not _is_command_available_channel(command, interaction):
        return False
    return await _is_command_checks_passed(command, interaction)


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
