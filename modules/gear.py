import discord
from discord.ext import commands

import re

import utils.image_processing as improc
import utils.discord_utils as utils

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
    
        self.gear_help = discord.Embed(title="Gear help",
                                       colour=cfg.embed_color)
    
        # "ap"|"aap"|"dp"|"acc"|"dr"|"eva"|"hp"|"all ap"|"all aap"|"class"|"level"
        # "dr_rate"|"se_rate"
        # "plan"
        # "gear"
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Gear module is now running.")
    
    
    @commands.group(pass_context=True, invoke_without_command=True)
    async def gear(self, ctx: commands.Context, *args):
        async with ctx.channel.typing():
            user_id = utils.get_user(ctx, args)
            await self.post_gear(ctx, user_id)
    
    
    @gear.group(pass_context=True, invoke_without_command=True)
    async def set(self, ctx: commands.Context, *, params: str = None):
        async with ctx.channel.typing():
            if await self.process_stats(ctx, params):
                await ctx.send("Gear has been updated.")
                await self.post_gear(ctx, ctx.author.id)
            else:
                await ctx.send("Something went wrong!")

    
    @set.command()
    async def garmoth(self, ctx: commands.Context, link = None):
        # Take link as a arg, if not supplied, check database 
        async with ctx.channel.typing():
            if link is not None:
                pass
            elif(db.contains(ctx.author.id)):
                pass
            else:
                ctx.send("You have to provide garmoth.com link or have it already set in your gear set.")
                return
        
    
    @gear.command()
    async def remove(self, ctx: commands.Context, *args):
        async with ctx.channel.typing():
            user_id = utils.get_user(ctx, args)
            if not db.contains(table="gear", condition=f"user_id={user_id}"):
                await ctx.send("User hasn't created a gear build.")
                return

            db.delete(table="gear", condition=f"user_id={user_id}")
            await ctx.send("User has been deleted.")
    
    
    @gear.command()
    async def help(self, ctx: commands.Context, *args):
        async with ctx.channel.typing():
            await ctx.send(embed=self.gear_help)
        
    
    async def post_gear(self, ctx: commands.Context, user_id: str):
        try:
            """ db.select(values="*", 
                      table="gear", 
                      condition=f"user_id={user_id}")
            res = db.fetchone()
            
            _, ap, aap, dp, health, all_ap, all_aap, accuracy, dr, dr_rate, evasion, se_rate, player_class, level, planner, _ = res """
            ap, aap, dp, health, all_ap, all_aap, accuracy, dr, dr_rate, evasion, se_rate, player_class, level, planner = \
            100, 100, 300, 5000, 600, 600, 800, 300, 30, 600, 20, "Striker", 63.3, ""
            
            embed = discord.Embed(title="Gear Set",
                      description=f"""{ctx.author.mention}
                                      ```Class: {player_class}, Level: {level}, Gear Score: {self.gearscore(ap, aap, dp):.1f}```
                                      [Garmoth planner](f{planner})""")

            embed.add_field(name="AP",
                            value=f"{ap}")
            embed.add_field(name="AAP",
                            value=f"{aap}")
            embed.add_field(name="DP",
                            value=f"{dp}")
            embed.add_field(name="Accuracy",
                            value=f"{accuracy}")
            embed.add_field(name="DR",
                            value=f"{dr} + {dr_rate} %")
            embed.add_field(name="Evasion",
                            value=f"{evasion} + {se_rate} %")

            photo = discord.File("data\\gear\\a.png")
            
            embed.set_image(url="attachment://a.png")

            await ctx.send(embed=embed, file=photo)
        except Exception as e:
            print(e)
    
    
    async def process_stats(self, ctx: commands.Context, params: str) -> bool:
        if params == None: return False
        try:
            parsed = {}
            for param in params.split(';'):
                name, value = param.split('=')
                name, value = name.strip().lower(), value.strip()
                match name:
                    case "ap"|"aap"|"dp"|"acc"|"dr"|"eva"|"hp"|"all_ap"|"all_aap"|"class"|"level":
                        parsed[name] = int(value)
                        
                    case "dr_rate"|"se_rate":
                        parsed[name] = re.match(r"\d+(\.|,)?\d+", value).group()
                        
                    case "plan":
                        if re.match(r"(https:\/\/|http:\/\/|www.)garmoth.com\/character\/[0-9a-zA-Z]+") is None:
                            return False
                        
                        parsed[name] = f"\"{value}\""
                    
                    case "gear":
                        has_gear_img = 1
                        img_path = f"{cfg.gear.path}\\{ctx.author.id}.png"
                        
                        if value in ("None", "none"):
                            has_gear_img = 0
                            utils.delete_image(img_path)
                            
                        elif bool(value):
                            img = utils.get_image_from_url(value)
                            improc.resize_and_save(img, img_path, (cfg.gear.img_width, cfg.gear.img_height))
                                
                        elif bool(ctx.message.attachments):
                            img = utils.get_image_from_attachment(ctx.message.attachments[0])
                            improc.resize_and_save(img, img_path, (cfg.gear.img_width, cfg.gear.img_height))
                        
                        else:
                            raise Exception("Wrong value passed for gear.")
                        
                        parsed[name] = has_gear_img
                    
                    case _:
                        return False
                    
            db.update(values=f"{', '.join([f'{key}={val}' for key, val in parsed.items()])}",
                      table="gear",
                      condition=f"user_id={ctx.author.id}")
            db.commit()
        
        except Exception as e:
            print(e.with_traceback())
            return False
        
        return True
    
    
    def gearscore(self, ap: int, aap: int, dp: int) -> int|float:
        return (ap + aap) / 2 + dp
    
    
    
async def setup(client):
    await client.add_cog(Gear(client))