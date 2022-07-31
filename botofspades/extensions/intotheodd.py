from discord.ext import commands
from voladice import D6, D20

from botofspades.unicode import FIELD_ARROW
from botofspades.log import extension_loaded, extension_unloaded


EXTENSION_NAME: str = "Into the Odd"


class IntoTheOdd(commands.Cog):
    @commands.group(invoke_without_command=True, aliases=["ito"])
    async def intotheodd(self, ctx) -> None:
        ...

    @intotheodd.command(aliases=["r"])
    async def roll(self, ctx) -> None:
        await ctx.send(f"{ctx.author.mention} {D20.roll().get_total()}")

    @intotheodd.command(aliases=["rollatts", "ratts", "ra"])
    async def rollattributes(self, ctx) -> None:
        strength, dexterity, willpower = 0, 0, 0
        roll_amount: int = 0

        while max(strength, dexterity, willpower) < 10:
            strength, dexterity, willpower = [
                D6.rollmany(3).get_total() for _ in range(3)
            ]

            roll_amount += 1

        await ctx.send(
            f"{ctx.author.mention}\n"
            f"Strength {FIELD_ARROW} {strength}\n"
            f"Dexterity {FIELD_ARROW} {dexterity}\n"
            f"Willpower {FIELD_ARROW} {willpower}\n"
            + (f"\nRerolls: {roll_amount - 1}" if roll_amount > 1 else "")
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(IntoTheOdd())
    extension_loaded(EXTENSION_NAME)


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog("IntoTheOdd")
    extension_unloaded(EXTENSION_NAME)
