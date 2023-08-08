import discord
from discord.ext import commands

class Gear(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Gear module is now running.")
    
    
    @commands.group(pass_context=True, invoke_without_command=True)
    async def gear(self, ctx: commands.Context, *args):
        pass
    
    
    @gear.group(pass_context=True, invoke_without_command=True)
    async def update(self, ctx: commands.Context, *args):
        pass

    
    @update.command()
    async def garmoth(self, ctx: commands.Context, *args):
        pass
    
    
    @gear.command()
    async def remove(self, ctx: commands.Context, *args):
        pass
    
    
    def post_gear(self, user: discord.User):
        pass


    def gearscore(self, ap: int, aap: int, dp: int):
        return (ap + aap) / 2 + dp
    
    
    
async def setup(client):
    await client.add_cog(Gear(client))