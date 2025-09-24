from datetime import datetime
from typing import Any, Self

from discord import Color, Embed, Interaction, Member, User
from discord.app_commands import Command, ContextMenu
from discord.types.embed import EmbedType

from . import errors
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
        timestamp: datetime | None = None,
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
        timestamp: datetime | None = None,
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
            if isinstance(self.error, errors.CustomError):
                self.title = self.error.name
            elif self.error.__class__.__module__ in (None, object.__module__):
                self.title = self.error.__class__.__name__
            else:
                self.title = f"{self.error.__class__.__module__}.{self.error.__class__.__name__}"
        if self.description is None:
            self.description = str(self.error)
        if self.color is None:
            self.color = Color.red()

        if isinstance(self.command, Command):
            app_cmd = self.client.tree.get_app_command(self.command)
            if app_cmd is not None:
                self.add_field(name="Command", value=app_cmd.mention)
            else:
                self.add_field(name="Command", value=f"/{self.command.qualified_name}")
        elif isinstance(self.command, ContextMenu):
            self.add_field(name="Command", value=self.command.name)

        if self.user is not None:
            self.add_field(name="User", value=self.user.mention)
