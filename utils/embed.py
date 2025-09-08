import datetime
from collections.abc import Iterable, Mapping
from typing import Any, Self

from discord import Color, Embed, Interaction, Member, User
from discord.app_commands import AppCommand, AppCommandGroup, Command, ContextMenu, Group
from discord.ext.commands import Cog
from discord.types.embed import EmbedType

from .types import CielType


class ErrorEmbed(Embed):
    @classmethod
    def from_interaction(
        cls,
        error: Exception,
        interaction: Interaction,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> Self:
        client: CielType = interaction.client  # pyright: ignore[reportAssignmentType]
        user = interaction.user
        command = interaction.command
        if isinstance(command, (Command)):
            command = client.tree.get_app_command(command) or command

        return cls(
            error=error,
            user=user,
            command=command,
            colour=colour,
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    def __init__(
        self,
        error: Exception,
        user: User | Member | None = None,
        command: Command | ContextMenu | AppCommand | AppCommandGroup | None = None,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> None:
        self.error = error
        self.user = user
        self.command = command

        if title is None:
            if error.__class__.__module__ in (None, object.__module__):
                title = error.__class__.__name__
            else:
                title = f"{error.__class__.__module__}.{error.__class__.__name__}"
        if description is None:
            description = f"{error}"
        if colour is None:
            colour = Color.red()

        super().__init__(
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

        if command:
            if isinstance(command, (AppCommand, AppCommandGroup)):
                self.add_field(name="Command", value=command.mention)
            elif isinstance(command, Command):
                self.add_field(name="Command", value=f"/{command.qualified_name}")
            else:
                self.add_field(name="Command", value=command.name)
        if user:
            self.add_field(name="User", value=user.mention)


class ExtensionEmbed(Embed):
    @classmethod
    def from_client(
        cls,
        client: CielType,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> Self:
        return cls(
            client.extension_files(),
            client.extensions,
            colour=colour,
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    def __init__(
        self,
        extension_files: Iterable[str],
        extension_loaded: Iterable[str],
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> None:
        extension_files = set(extension_files)
        extension_loaded = set(extension_loaded)
        self.loaded = sorted(extension_loaded)
        self.not_loaded = sorted(extension_files - extension_loaded)
        self.missing_file = sorted(extension_loaded - extension_files)

        super().__init__(
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.add_field(name="Loaded Extensions", value="\n".join(self.loaded) or "No Extensions")
        self.add_field(name="Not Loaded Extensions", value="\n".join(self.not_loaded) or "No Extensions")
        self.add_field(name="Missing File Extensions", value="\n".join(self.missing_file) or "No Extensions")


class CommandMapEmbed(Embed):
    @classmethod
    def from_client(
        cls,
        client: CielType,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> Self:
        return cls(
            client.tree.command_map,
            [c for cog_name in client.cogs if (c := client.get_cog(cog_name))],
            colour=colour,
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    def __init__(
        self,
        command_map: Mapping[Command, AppCommand | AppCommandGroup],
        cogs: Iterable[Cog],
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> None:
        self.command_map = command_map
        self.unmapped = set(command_map.values())
        super().__init__(
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        for cog in cogs:
            lines = []
            cmds = cog.get_app_commands()
            while cmds:
                cmd = cmds.pop(0)
                if isinstance(cmd, Group):
                    cmds = cmd.commands + cmds
                    continue

                app_cmd = command_map.get(cmd)
                if app_cmd:
                    lines.append(f"`{cmd.qualified_name}` -> {app_cmd.mention}")
                    self.unmapped.discard(app_cmd)
                else:
                    lines.append(f"`{cmd.qualified_name}` -> None")
            self.add_field(name=cog.qualified_name, value="\n".join(lines) or "No Commands")
        self.add_field(
            name="Unmapped Commands",
            value="\n".join([cmd.mention for cmd in self.unmapped]) or "No Commands",
        )
