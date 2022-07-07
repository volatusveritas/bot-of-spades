from discord.ext import commands

from shutsubot import constants


class Shutsubot(commands.Bot):
    def load_default_exts(self):
        for ext in constants.DEFAULT_EXTENSIONS:
            self.load_extension(f"shutsubot.extensions.{ext}")


bot = Shutsubot(constants.PREFIXES)
bot.load_default_exts()
bot.run(constants.TOKEN)
