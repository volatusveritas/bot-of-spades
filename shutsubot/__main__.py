from discord.ext import commands

from shutsubot import constants


class Shutsubot(commands.Bot):
    def load_default_exts(self):
        self.load_extension("shutsubot.extensions.nightmare_generator")


bot = Shutsubot(constants.PREFIXES)
bot.load_default_exts()
bot.run(constants.TOKEN)
