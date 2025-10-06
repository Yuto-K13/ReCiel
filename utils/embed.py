from datetime import datetime
from typing import Any, Self

from discord import ClientUser, Color, Embed, Interaction, Member, User
from discord.app_commands import Command, ContextMenu
from discord.types.embed import EmbedType

from . import errors
from .types import CielType


class CustomEmbed(Embed):
    def __init__(
        self,
        user: User | Member | ClientUser | None,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        self.user = user
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

    @property
    def default_title(self) -> Any | None:  # noqa: ANN401
        return None

    @property
    def default_description(self) -> Any | None:  # noqa: ANN401
        return None

    @property
    def default_color(self) -> int | Color | None:
        return None

    def format(self) -> None:
        if self.title is None:
            self.title = self.default_title
        if self.description is None:
            self.description = self.default_description
        if self.color is None:
            self.color = self.default_color

        self.format_fields()
        self.format_footer()

    def format_fields(self) -> None: ...

    def format_footer(self) -> None:
        if self.user is not None:
            self.set_footer(text=f"Triggered by {self.user.display_name}", icon_url=self.user.display_avatar.url)


class ErrorEmbed(CustomEmbed):
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
        return cls(
            user=interaction.user,
            client=client,
            error=error,
            command=interaction.command,
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
        user: User | Member | ClientUser | None,
        client: CielType,
        error: Exception,
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
        self.command = command
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

    @property
    def default_title(self) -> str:
        if isinstance(self.error, errors.CustomError):
            return self.error.name
        if self.error.__class__.__module__ in (None, object.__module__):
            return self.error.__class__.__name__
        return f"{self.error.__class__.__module__}.{self.error.__class__.__name__}"

    @property
    def default_description(self) -> str:
        return str(self.error)

    @property
    def default_color(self) -> int | Color:
        return Color.red()

    def format_fields(self) -> None:
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

    def format_footer(self) -> None:
        user = self.user or self.client.user
        if user is not None:
            self.set_footer(text=f"Caused by {user.display_name}", icon_url=user.display_avatar.url)
