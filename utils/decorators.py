from discord import Interaction, app_commands

from .error import DeveloperCommandError
from .types import CielType


def developer_only():  # noqa: ANN201
    async def predicate(interaction: Interaction) -> bool:
        client: CielType = interaction.client  # pyright: ignore[reportAssignmentType]
        if not await client.is_owner(interaction.user):
            raise DeveloperCommandError
        return True

    return app_commands.check(predicate)
