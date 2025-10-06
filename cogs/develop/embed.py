from datetime import datetime
from typing import Any

from discord import ClientUser, Color, Member, User
from discord.app_commands import Command
from discord.enums import AppCommandType
from discord.types.embed import EmbedType

import utils
from utils.types import CielType


class ExtensionEmbed(utils.CustomEmbed):
    def __init__(
        self,
        user: User | Member | ClientUser | None,
        client: CielType,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        self.client = client
        super().__init__(
            user=user,
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    def format_fields(self) -> None:
        extension_files = set(self.client.extension_files())
        extension_loaded = set(self.client.extensions)
        self.loaded = sorted(extension_loaded)
        self.not_loaded = sorted(extension_files - extension_loaded)
        self.missing_file = sorted(extension_loaded - extension_files)

        self.add_field(name="Loaded Extensions", value="\n".join(self.loaded) or "No Extensions")
        self.add_field(name="Not Loaded Extensions", value="\n".join(self.not_loaded) or "No Extensions")
        self.add_field(name="Missing File Extensions", value="\n".join(self.missing_file) or "No Extensions")


class CommandMapEmbed(utils.CustomEmbed):
    def __init__(
        self,
        user: User | Member | ClientUser | None,
        client: CielType,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        self.client = client
        super().__init__(
            user=user,
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    def format_fields(self) -> None:
        self.unmapped = set(self.client.tree.command_map.values())
        self.guild_map: dict[Command, str] = {}

        for guild in (None, *self.client.guilds):
            cmds = self.client.tree.get_commands(guild=guild, type=AppCommandType.chat_input)
            for cmd in utils.expand_commands(cmds):
                self.guild_map[cmd] = guild.name if guild is not None else "Global"

        for cog_name in self.client.cogs:
            cog = self.client.get_cog(cog_name)
            if cog is None:
                continue
            lines = []
            for cmd in utils.expand_commands(cog.get_app_commands()):
                app_cmd = self.client.tree.get_app_command(cmd)
                guild_name = self.guild_map.get(cmd, "Unknown Guild")
                if app_cmd is not None:
                    lines.append(f"`{cmd.qualified_name}` -> {app_cmd.mention} ({guild_name})")
                    self.unmapped.discard(app_cmd)
                else:
                    lines.append(f"`{cmd.qualified_name}` -> None ({guild_name})")
            self.add_field(name=cog.qualified_name, value="\n".join(lines) or "No Commands")

        self.add_field(
            name="Unmapped Commands",
            value="\n".join([cmd.mention for cmd in self.unmapped]) or "No Commands",
        )
