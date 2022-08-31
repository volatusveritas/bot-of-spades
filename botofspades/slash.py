from discord.ext import commands
from discord import app_commands as apc

from botofspades import constants


def add_slash_command(
    bot: commands.Bot, command: apc.Command | apc.Group
) -> None:
    bot.tree.add_command(command, guild=constants.TARGET_GUILD)


def remove_slash_command(bot: commands.Bot, command_name: str) -> None:
    bot.tree.remove_command(command_name, guild=constants.TARGET_GUILD)
