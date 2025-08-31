from discord import Interaction, app_commands
from discord.app_commands import CheckFailure
from discord.ext.commands import Bot


def developer_only():
    async def predicate(interaction: Interaction) -> bool:
        client = interaction.client
        if not isinstance(client, Bot):
            raise CheckFailure("Client is not Bot")
        if not await client.is_owner(interaction.user):
            raise CheckFailure("開発者専用コマンドです。")
        return True

    return app_commands.check(predicate)
