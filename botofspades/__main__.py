import asyncio

from discord import Object

from botofspades import constants
from botofspades.log import setup_logging
from botofspades.outmsg import update_defbank
from botofspades.bot import bot


with open(".SERVER_ID") as id_file:
    constants.TARGET_GUILD = Object(int(id_file.read()))

update_defbank()
setup_logging()

with open(".BOT_TOKEN") as token_file:
    TOKEN: str = token_file.read()

asyncio.run(bot.load_default_exts())
bot.run(TOKEN)
