from discord.ext import commands

from botofspades import constants


class BotOfSpades(commands.Bot):
    def load_default_exts(self) -> None:
        for ext in constants.DEFAULT_EXTENSIONS:
            self.load_extension(f"shutsubot.extensions.{ext}")


bot: BotOfSpades = BotOfSpades(constants.PREFIXES)
bot.load_default_exts()
bot.run(constants.TOKEN)
