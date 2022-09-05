from discord import Interaction
from discord.ext import commands
from discord import app_commands as apc

from botofspades import constants
from botofspades.bot import bot
from botofspades.log import extension_loaded, extension_unloaded
from botofspades.outmsg import botsend, update_defbank
from botofspades.slash import add_slash_command, remove_slash_command


EXTENSION_NAME: str = "Bot Control"


@apc.command()
async def reload(itr: Interaction) -> None:
    for ext in constants.DEFAULT_EXTENSIONS:
        await bot.reload_extension(f"botofspades.extensions.{ext}")

    await bot.tree.sync(guild=constants.TARGET_GUILD)

    update_defbank()

    await botsend(itr, "Bot reloaded.")


async def setup(bot: commands.Bot) -> None:
    add_slash_command(bot, reload)
    extension_loaded(EXTENSION_NAME)


async def teardown(bot: commands.Bot) -> None:
    remove_slash_command(bot, "reload")
    extension_unloaded(EXTENSION_NAME)
