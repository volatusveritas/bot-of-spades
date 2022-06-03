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
PSYCHEE_LEVEL_BOOST: int = 3
PSYCHEE_VITALITY_BOOST: int = 4
PSYCHEE_HURT_BOOST: int = 3
PSYCHEE_LEVEL_CHANCE_BIAS: float = 1.0
OVERLORD_CHANCE: float = 5.0 # In percentage
OVERLORD_LEVEL_BOOST: int = 5
OVERLORD_VITALITY_BOOST: int = 7
OVERLORD_HURT_BOOST: int = 5
OVERLORD_LEVEL_CHANCE_BIAS: float = 0.5
MIN_VITALITY: int = 2 # Per level
MAX_VITALITY: int = 4 # Per level
MIN_HURT: int = 1 # Per level
MAX_HURT: int = 3 # Per level


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
            type: str = random.choice(TYPES)
            level: int = random.randint(min_level, max_level)
            vitality: int = random.randint(MIN_VITALITY, MAX_VITALITY)*level
            hurt: int = random.randint(MIN_HURT, MAX_HURT)

            is_psychee: bool = (
                utils.random.percentage() + PSYCHEE_LEVEL_CHANCE_BIAS * level
            ) <= PSYCHEE_CHANCE
            is_overlord: bool = (
                utils.random.percentage() + OVERLORD_LEVEL_CHANCE_BIAS * level
            ) <= OVERLORD_CHANCE

            if is_psychee:
                level += PSYCHEE_LEVEL_BOOST
                vitality += PSYCHEE_VITALITY_BOOST
                hurt += PSYCHEE_HURT_BOOST
            if is_overlord:
                level += OVERLORD_LEVEL_BOOST
                vitality += OVERLORD_VITALITY_BOOST
                hurt += OVERLORD_HURT_BOOST

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
                "Level %d %s (%s): Vitality %d, Hurt %d\n" % (
                    level, type, extra_descriptor, vitality, hurt
                )
            )

        await ctx.send(nightmares)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(NightmareGenerator(bot))
