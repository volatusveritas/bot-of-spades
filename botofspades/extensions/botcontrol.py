from discord.ext import commands

from botofspades import constants
from botofspades.log import extension_loaded, extension_unloaded


EXTENSION_NAME: str = "Bot Control"


class BotControl(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command()
    async def reload(self, ctx) -> None:
        for ext in constants.DEFAULT_EXTENSIONS:
            self.bot.reload_extension(f"botofspades.extensions.{ext}")

        await ctx.message.reply("Extensions reloaded.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(BotControl(bot))
    extension_loaded(EXTENSION_NAME)


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog("BotControl")
    extension_unloaded(EXTENSION_NAME)
