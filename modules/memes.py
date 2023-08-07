import discord
from discord.ext import commands

class Memes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Memes module is now running.")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        pass
    
    
    
async def setup(client):
    await client.add_cog(Memes(client))