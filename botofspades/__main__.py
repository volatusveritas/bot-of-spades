from discord.ext import commands

from botofspades import constants
from botofspades.log import logger, setup_logging


class BotOfSpades(commands.Bot):
    def load_default_exts(self) -> None:
        for ext in constants.DEFAULT_EXTENSIONS:
            self.load_extension(f"botofspades.extensions.{ext}")

    async def on_ready(self) -> None:
        logger.info("Bot ready to receive commands")


setup_logging()

bot: BotOfSpades = BotOfSpades(constants.PREFIXES)
bot.load_default_exts()
bot.run(constants.TOKEN)
