from datetime import datetime
from typing import Any

from discord import Color, Embed, Interaction
from discord.types.embed import EmbedType
from discord.ui import Item, View

TIMEOUT = 180


class CustomView(View):
    def __init__(self, interaction: Interaction, *, timeout: float | None = TIMEOUT) -> None:
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.client = interaction.client
        self.embed_kwargs: dict[str, Any] = {}

    async def on_error(self, interaction: Interaction, error: Exception, item: Item) -> None:
        kwargs = {"view": self, "item": item}
        self.client.dispatch("interaction_error", interaction, error, **kwargs)

    async def on_timeout(self) -> None:
        await self.interaction.edit_original_response(view=None)

    @property
    def embed(self) -> Embed:
        return Embed(**self.embed_kwargs)

    def set_embed(
        self,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> Embed:
        self.embed_kwargs = {
            "colour": colour,
            "color": color,
            "title": title,
            "type": type,
            "url": url,
            "description": description,
            "timestamp": timestamp,
        }
        return self.embed
