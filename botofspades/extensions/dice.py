import random

from discord.ext import commands

from shutsubot import unicode


class Dice(commands.Cog):
    @commands.command(aliases=["r"])
    async def roll(self, ctx, attr_val:int=0) -> None:
        dice_results: list[int] = []
        highest_val: int = 0
        high_pos: int = -1
        for i in range(attr_val):
            result = random.randint(1, 6)
            if result > highest_val:
                highest_val = result
                high_pos = i

            dice_results.append(result)

        formatted_output: str = "["

        for i in range(len(dice_results)):
            if i == high_pos:
                formatted_output += f"**{dice_results[i]}**"
            else:
                formatted_output += str(dice_results[i])

            if i != len(dice_results) - 1:
                formatted_output += ", "

        formatted_output += f"]  {unicode.DICE_ARROW}  ({highest_val}) "

        if highest_val <= 2:
            formatted_output += "Falha com consequências"
        elif highest_val <= 4:
            formatted_output += "Acerto com consequências"
        else:
            formatted_output += "Acerto sem consequências"

        formatted_output += f"\n{ctx.author.mention}"

        await ctx.send(formatted_output)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Dice())


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog("Dice")
