import datetime
from collections.abc import Iterable
from typing import Any, Self

from discord import Color, Embed, Interaction, Member, User
from discord.app_commands import AppCommand, AppCommandGroup, Command
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
        command: Command | AppCommand | AppCommandGroup | None = None,
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
                self.add_field(name="App Command", value=command.mention)
            else:
                self.add_field(name="Command", value=f"/{command.qualified_name}")
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
