import discord
from discord.ext import commands

from config import cfg
from database import db

""" SAVED IN DATABASE:
        user_id INTEGER PRIMARY KEY, 
        ap INTEGER, 
        aap INTEGER,
        dp INTEGER,
        health INTEGER, 
        all_ap INTEGER,
        all_aap INTEGER,
        accuracy INTEGER, 
        dr TEXT,
        dr_rate INTEGER, 
        evasion TEXT,
        se_rate INTEGER,
        class TEXT, 
        level REAL,
        gear_planner TEXT,
        gear_image INTEGER 
"""

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