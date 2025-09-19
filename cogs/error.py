from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

import utils
from utils.types import CielType


class ErrorCog(commands.Cog, name="Error"):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction_error(self, interaction: Interaction, error: Exception, /, **kwargs: object) -> None:
        if not isinstance(error, utils.CustomError) or not error.ignore:
            texts = [
                f"User: {interaction.user.display_name}",
                f"Guild: {interaction.guild}",
                f"Channel: {interaction.channel}",
            ]
            for key, value in kwargs.items():
                texts.append(f"{key.title()}: {value}")

            utils.logger.exception(", ".join(texts), exc_info=error)

        embed = utils.ErrorEmbed.from_interaction(client=self.bot, error=error, interaction=interaction)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()
            return
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="raise")
    @utils.developer_only()
    async def raise_error(self, interaction: Interaction) -> None:
        """Raise a test error."""
        embed = Embed(title="Raising TestError", color=Color.light_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        raise utils.CustomError("Raised TestError", name="TestError")


async def setup(bot: CielType) -> None:
    await bot.add_cog(ErrorCog(bot))
