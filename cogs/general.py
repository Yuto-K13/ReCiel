from typing import Union

from discord import Color, Embed, Interaction, app_commands
from discord.app_commands import AppCommand, AppCommandGroup, Argument, Command, Group
from discord.ext import commands

from ciel import Ciel


class General(commands.Cog):
    def __init__(self, bot: Ciel):
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: Interaction):
        """応答速度の表示"""
        latency = self.bot.latency * 1000
        embed = Embed(title="Pong!", color=Color.blue())
        embed.add_field(name="Latency", value=f"{latency:.2f} ms", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def help(self, interaction: Interaction):
        """コマンドの詳細説明"""

        def descriptions(
            command: Union[Command, Group],
            app_command: Union[AppCommand, AppCommandGroup],
        ) -> list[str]:
            descs: list[str] = list()
            if isinstance(command, Command):
                descs.append(app_command.mention)
                descs.append(command.description)
                if command.parameters:
                    descs.append("**Parameters**")
                for param in command.parameters:
                    descs.append(f"・{param.name}: {param.description}")
                return descs

            sub_command_map = {
                sub_command: sub_app_command
                for sub_command in command.commands
                for sub_app_command in app_command.options
                if sub_command.name == sub_app_command.name
            }
            for sub_command in command.commands:
                sub_app_command = sub_command_map.get(sub_command)
                if sub_app_command is None or isinstance(sub_app_command, Argument):
                    continue
                descs.extend(descriptions(sub_command, sub_app_command))
            return descs

        global_commands = await self.bot.tree.fetch_commands()
        guild_commands = await self.bot.tree.fetch_commands(guild=interaction.guild)
        app_command_map = {cmd.name: cmd for cmd in global_commands + guild_commands}

        embed = Embed(title="Help for Ciel", color=Color.blue())
        for cog_name in self.bot.cogs:
            cog = self.bot.get_cog(cog_name)
            if cog is None:
                continue

            descs = list()
            for command in cog.get_app_commands():
                app_command = app_command_map.get(command.name)
                if app_command is None:
                    continue
                descs.extend(descriptions(command, app_command))
            if descs:
                embed.add_field(name=cog_name, value="\n".join(descs))
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: Ciel):
    await bot.add_cog(General(bot))
