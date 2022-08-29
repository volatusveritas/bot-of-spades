from discord.ext import commands

from botofspades import constants
from botofspades.log import extension_loaded, extension_unloaded
from botofspades.outmsg import botsend, update_defbank


EXTENSION_NAME: str = "Bot Control"


class BotControl(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command()
    async def reload(self, ctx) -> None:
        for ext in constants.DEFAULT_EXTENSIONS:
            await self.bot.reload_extension(f"botofspades.extensions.{ext}")

        update_defbank()

        await botsend(ctx, "Bot reloaded.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BotControl(bot))
    extension_loaded(EXTENSION_NAME)


async def teardown(bot: commands.Bot) -> None:
    await bot.remove_cog("BotControl")
    extension_unloaded(EXTENSION_NAME)
