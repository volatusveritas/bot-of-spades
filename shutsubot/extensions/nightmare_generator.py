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
PSYCHEE: dict = {
    "CHANCE": 5.0,
    "LEVEL_BOOST": 3,
    "VITALITY_BOOST": 4,
    "HURT_BOOST": 3,
    "LEVEL_CHANCE_BIAS": 1.0
}
OVERLORD: dict = {
    "CHANCE": 2.5,
    "LEVEL_BOOST": 5,
    "VITALITY_BOOST": 7,
    "HURT_BOOST": 5,
    "LEVEL_CHANCE_BIAS": 0.5
}
MIN_VITALITY: int = 2 # Per level
MAX_VITALITY: int = 4 # Per level
MIN_HURT: int = 1 # Per level
MAX_HURT: int = 3 # Per level
MIN_LEVEL: int = 1
MAX_LEVEL: int = 20


class NightmareGenerator(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(aliases=("gen",))
    async def generate(
        self, ctx: commands.Context,
        amount: int = 1,
        level_specifier: str = "1-4"
    ) -> None:
        min_level: int = 0
        max_level: int = 0

        if "-" in level_specifier:
            if level_specifier[0] == "-":
                min_level = MIN_LEVEL
                max_level = int(level_specifier[1:])
            elif level_specifier[-1] == "-":
                min_level = int(level_specifier[:-1])
                max_level = MAX_LEVEL
            else:
                level_args = level_specifier.split("-")
                min_level = int(level_args[0])
                max_level = int(level_args[1])
        else:
            min_level = int(level_specifier)
            max_level = min_level

        nightmares: str = ""

        for _i in range(amount):
            type: str = random.choice(TYPES)
            level: int = random.randint(min_level, max_level)
            vitality: int = random.randint(MIN_VITALITY, MAX_VITALITY)*level
            hurt: int = random.randint(MIN_HURT, MAX_HURT)

            is_psychee: bool = (
                utils.random.percentage() + PSYCHEE["LEVEL_CHANCE_BIAS"]*level
            ) <= PSYCHEE["CHANCE"]
            is_overlord: bool = (
                utils.random.percentage() + OVERLORD["LEVEL_CHANCE_BIAS"]*level
            ) <= OVERLORD["CHANCE"]

            if is_psychee:
                level += PSYCHEE["LEVEL_BOOST"]
                vitality += PSYCHEE["VITALITY_BOOST"]
                hurt += PSYCHEE["HURT_BOOST"]
            if is_overlord:
                level += OVERLORD["LEVEL_BOOST"]
                vitality += OVERLORD["VITALITY_BOOST"]
                hurt += OVERLORD["HURT_BOOST"]

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
