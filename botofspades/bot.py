from discord.ext import commands
from discord import Intents

from botofspades import constants
from botofspades.log import logger


def get_bot_intents() -> Intents:
    intents: Intents = Intents.default()
    intents.message_content = True
    return intents


class BotOfSpades(commands.Bot):
    async def load_default_exts(self) -> None:
        for ext in constants.DEFAULT_EXTENSIONS:
            await self.load_extension(f"botofspades.extensions.{ext}")

    async def on_ready(self) -> None:
        await self.tree.sync(guild=constants.TARGET_GUILD)
        logger.info("Bot ready to receive commands")


bot: BotOfSpades = BotOfSpades(
    command_prefix=constants.PREFIXES,
    intents=get_bot_intents()
)
