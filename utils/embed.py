import datetime
from typing import Any, Self

from discord import Color, Embed, Interaction, Member, User
from discord.app_commands import Command, ContextMenu
from discord.enums import AppCommandType
from discord.types.embed import EmbedType

from .commands import expand_commands
from .types import CielType


class ErrorEmbed(Embed):
    @classmethod
    def from_interaction(
        cls,
        client: CielType,
        error: Exception,
        interaction: Interaction,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> Self:
        user = interaction.user
        command = interaction.command

        return cls(
            client=client,
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
        client: CielType,
        error: Exception,
        user: User | Member | None = None,
        command: Command | ContextMenu | None = None,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> None:
        self.client = client
        self.error = error
        self.user = user
        self.command = command
        super().__init__(
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.format()

    def format(self) -> None:
        if self.title is None:
            if self.error.__class__.__module__ in (None, object.__module__):
                self.title = self.error.__class__.__name__
            else:
                self.title = f"{self.error.__class__.__module__}.{self.error.__class__.__name__}"
        if self.description is None:
            self.description = str(self.error)
        if self.color is None:
            self.color = Color.red()

        if isinstance(self.command, Command):
            if app_cmd := self.client.tree.get_app_command(self.command):
                self.add_field(name="Command", value=app_cmd.mention)
            else:
                self.add_field(name="Command", value=f"/{self.command.qualified_name}")
        elif isinstance(self.command, ContextMenu):
            self.add_field(name="Command", value=self.command.name)
        if self.user:
            self.add_field(name="User", value=self.user.mention)


class ExtensionEmbed(Embed):
    def __init__(
        self,
        client: CielType,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> None:
        self.client = client
        super().__init__(
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.format()

    def format(self) -> None:
        extension_files = set(self.client.extension_files())
        extension_loaded = set(self.client.extensions)
        self.loaded = sorted(extension_loaded)
        self.not_loaded = sorted(extension_files - extension_loaded)
        self.missing_file = sorted(extension_loaded - extension_files)

        self.add_field(name="Loaded Extensions", value="\n".join(self.loaded) or "No Extensions")
        self.add_field(name="Not Loaded Extensions", value="\n".join(self.not_loaded) or "No Extensions")
        self.add_field(name="Missing File Extensions", value="\n".join(self.missing_file) or "No Extensions")


class CommandMapEmbed(Embed):
    def __init__(
        self,
        client: CielType,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime.datetime | None = None,
    ) -> None:
        self.client = client
        super().__init__(
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.format()

    def format(self) -> None:
        self.unmapped = set(self.client.tree.command_map.values())
        self.guild_map: dict[Command, str] = {}
        for guild in (None, *self.client.guilds):
            for cmd in expand_commands(self.client.tree.get_commands(guild=guild, type=AppCommandType.chat_input)):
                self.guild_map[cmd] = guild.name if guild else "Global"

        for cog_name in self.client.cogs:
            cog = self.client.get_cog(cog_name)
            if cog is None:
                continue
            lines = []
            for cmd in expand_commands(cog.get_app_commands()):
                app_cmd = self.client.tree.command_map.get(cmd)
                if app_cmd:
                    lines.append(f"`{cmd.qualified_name}` -> {app_cmd.mention} ({self.guild_map.get(cmd, 'Unknown')})")
                    self.unmapped.discard(app_cmd)
                else:
                    lines.append(f"`{cmd.qualified_name}` -> None ({self.guild_map.get(cmd, 'Unknown')})")
            self.add_field(name=cog.qualified_name, value="\n".join(lines) or "No Commands")

        self.add_field(
            name="Unmapped Commands",
            value="\n".join([cmd.mention for cmd in self.unmapped]) or "No Commands",
        )
