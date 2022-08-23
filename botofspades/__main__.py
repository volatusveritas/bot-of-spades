from discord.ext import commands

from botofspades import constants
from botofspades.log import logger, setup_logging
from botofspades.outmsg import update_defbank


class BotOfSpades(commands.Bot):
    def load_default_exts(self) -> None:
        for ext in constants.DEFAULT_EXTENSIONS:
            self.load_extension(f"botofspades.extensions.{ext}")

    async def on_ready(self) -> None:
        logger.info("Bot ready to receive commands")


update_defbank()
setup_logging()

# Read the bot's token from .BOT_TOKEN
with open(".BOT_TOKEN", "r") as token_file:
    TOKEN: str = token_file.read()

bot: BotOfSpades = BotOfSpades(constants.PREFIXES)
bot.load_default_exts()
bot.run(TOKEN)
