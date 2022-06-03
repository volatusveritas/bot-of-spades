import random

from discord.ext import commands

import utils.random


DANGER_LEVELS: list[str] = [
    "Sheep",
    "Wolf",
    "Anaconda",
    "Medusa",
    "Cerberus",
    "Profane",
    "Apocalyptic",
    "Incognito",
    "Exponentis"
]
TYPES: list[str] = [
    "Dreamfreaker",
    "Trail",
    "Odin",
    "Possessor",
    "Lightning",
    "Mimic",
    "Mindcrawler"
]
PSYCHEE_CHANCE: float = 2.0 # In percentage
OVERLORD_CHANCE: float = 5.0 # In percentage
PSYCHEE_LEVEL_BOOST: int = 0
OVERLORD_LEVEL_BOOST: int = 0
PSYCHEE_VITALITY_BOOST: int = 4
OVERLORD_VITALITY_BOOST: int = 7
MIN_VITALITY: int = 2 # Per level
MAX_VITALITY: int = 4 # Per level


class NightmareGenerator(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def generate(
        self, ctx: commands.Context,
        r_amount: str = "1",
        r_base_level: str = "1",
        r_ceil_level: str = "4"
    ) -> None:
        amount: int = int(r_amount)
        min_level: int = int(r_base_level)
        max_level: int = int(r_ceil_level)

        nightmares: str = ""

        for _i in range(amount):
            is_psychee: bool = utils.random.percentage() <= PSYCHEE_CHANCE
            is_overlord: bool = utils.random.percentage() <= OVERLORD_CHANCE

            type: str = random.choice(TYPES)
            danger_level: str = random.choice(DANGER_LEVELS)
            level: int = (
                random.randint(min_level, max_level)
                + PSYCHEE_LEVEL_BOOST*is_psychee
                + OVERLORD_LEVEL_BOOST*is_overlord
            )
            vitality: int = (
                random.randint(MIN_VITALITY, MAX_VITALITY)*level
                + PSYCHEE_VITALITY_BOOST*is_psychee
                + OVERLORD_VITALITY_BOOST*is_psychee
            )
            extra_descriptor: str = ""

            descriptors = []
            if is_psychee:
                descriptors.append("Psychee")
            if is_overlord:
                descriptors.append("Overlord")

            if not descriptors:
                extra_descriptor = "Normal"
            else:
                extra_descriptor = ", ".join(descriptors)

            nightmares += (
                "Level %d %s, %s (%s): %d/%d\n" % (
                    level, type, danger_level, extra_descriptor,
                    vitality, vitality
                )
            )

        await ctx.send(nightmares)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(NightmareGenerator(bot))
