from discord.ext import commands


class NightmareGenerator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def generate(self, ctx: commands.Context):
        await ctx.send("Not implemented.")


def setup(bot: commands.Bot):
    bot.add_cog(NightmareGenerator(bot))
