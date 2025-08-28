from discord import Interaction, app_commands
from discord.app_commands import CheckFailure

from ciel import Ciel


def developer_only():
    async def predicate(interaction: Interaction) -> bool:
        client = interaction.client
        if not isinstance(client, Ciel):
            raise CheckFailure("Client is not Ciel")
        if not await client.is_owner(interaction.user):
            raise CheckFailure("開発者専用コマンドです。")
        return True

    return app_commands.check(predicate)
