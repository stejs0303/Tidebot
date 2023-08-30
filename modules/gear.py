import discord
from discord.ext import commands
from discord.ext.commands import Context

from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep

import utils.image_processing as improc
import utils.discord_utils as utils

from typing import Any

from config import cfg
from database import db
from compiled_regex import regex


class Gear(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.gear_help = discord.Embed(title="Gear Help",
                                       colour=cfg.embed_color)
        self.gear_help.add_field(name=f"{cfg.prefix}gear / {cfg.prefix}gear @user",
                                 value="- posts embed containing user's gear.",
                                 inline=False)
        self.gear_help.add_field(name=f"{cfg.prefix}gear create / {cfg.prefix}gear create @user",
                                 value="- creates new gear in database.",
                                 inline=False)
        self.gear_help.add_field(name=f"{cfg.prefix}gear set",
                                 value=f"- allows user to set individual stats of their gearset.\n"
                                       f"- parameters:\n"
                                       f"```\n"
                                       f"ap, aap, dp, hp, total_ap, total_aap\n"
                                       f" - accepts a whole number\n"
                                       f"dr, evasion, accuracy\n"
                                       f" - accepts a whole number or a triplet (melee, ranged, magic)\n"
                                       f"dr_rate, se_rate\n"
                                       f" - accepts whole number folowed by percentage sign\n"
                                       f"plan\n"
                                       f" - accepts a garmoth.com gear planner\n"
                                       f"img\n"
                                       f" - accepts Image, URL link or None\n"
                                       f"class, level\n"
                                       f" - accepts text or floating point number"
                                       f"```\n"
                                       f"- to make change to multiple parameters, use a semicolon ' ; ' as a separator.\n"
                                       f"- keywords are not case sensitive.",
                                 inline=False)
        self.gear_help.add_field(name=f"{cfg.prefix}gear set garmoth *url*",
                                 value=f"- scrapes the garmoth.com website for all stats that you're able to set using normal method.\n"
                                       f"- stats are taken from the first gear build.",
                                 inline=False)
        self.gear_help.add_field(name=f"{cfg.prefix}gear remove / {cfg.prefix}gear remove @user",
                                 value="- removes gear from database",
                                 inline=False)
        self.gear_help.add_field(name="Example",
                                 value=f"```{cfg.prefix}gear create\n{cfg.prefix}gear set ap=301; dp= 395; dr =(430, 425, 425); dr_rate = 29%\n"
                                       f"{cfg.prefix}gear set img=www.somelinktoimage.com/a3k0by.png```",
                                 inline=False)
        

        self.has_gear = f"User has already set up his gearset. \
            For information how to set individial gear stats use `{cfg.prefix}gear help`."
        self.no_gear = f"User hasn\'t set up a gearset yet. \
            You can create a new gearset using `{cfg.prefix}gear create` command."
        
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Gear module is now running.")
    
    
    @commands.group(pass_context=True, invoke_without_command=True)
    async def gear(self, ctx: Context, *args):
        async with ctx.channel.typing():
            user_id = utils.get_user(ctx, args)
            if not db.contains(table="gear", condition=f"user_id={user_id}"): 
                await ctx.send(self.no_gear)
                return
            
            await self.post_gear(ctx, user_id)
    
    
    @gear.command()
    async def create(self, ctx: Context, *args):
        async with ctx.channel.typing():
            user_id = utils.get_user(ctx, args)
            if db.contains(table="gear", condition=f"user_id={user_id}"): 
                await ctx.send(self.has_gear)
                return
            
            db.insert(values=f"({user_id}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'Class', 0, '', 0)",
                      table="gear")
            db.commit()
            
            if db.contains(table="gear", condition=f"user_id={user_id}"):
                await ctx.send("Gearset has been created.")
            else:
                await ctx.send("Couldn\'t create gear.")
    
    
    @gear.group(pass_context=True, invoke_without_command=True)
    async def set(self, ctx: Context, *, params: str = None):
        async with ctx.channel.typing():
            if not db.contains(table="gear", condition=f"user_id={ctx.author.id}"): 
                await ctx.send(self.no_gear)
                return
            
            state, message = await self.process_stats(ctx, params)
            if state:
                await ctx.send("Gear has been updated.")
                await self.post_gear(ctx, ctx.author.id)
            else:
                await ctx.send(f"Error: {message}")

    
    @set.command()
    async def garmoth(self, ctx: Context, link = None):
        async with ctx.channel.typing():
            if not db.contains(table="gear", condition=f"user_id={ctx.author.id}"): 
                await ctx.send(self.no_gear)
                return
            
            if link is not None:
                if regex.garmoth_url.match(link) is None:
                    await ctx.send(f"Provided url {link} doesn\'t match garmoth.com gear build.")
                    return
            else:
                db.select(values=f"plan", 
                          table="gear", 
                          condition=f"user_id={ctx.author.id}")

                if not bool((link := db.fetchone()[0])):
                    await ctx.send("You have to provide garmoth.com link or have it already set in your gearset.")
                    return
        
            stats: dict = self.scrape_webpage_content(link)
            state, message = await self.process_stats(
                ctx, f"; ".join([f"{name}=\'{value}\'" for name, value in stats.items()]))
            
            if state:
                await ctx.send("Gear has been updated.")
                await self.post_gear(ctx, ctx.author.id)
            else:
                await ctx.send(f"Error: {message}")
                
                
    @gear.command()
    async def remove(self, ctx: Context, *args):
        async with ctx.channel.typing():
            user_id = utils.get_user(ctx, args)
            if not db.contains(table="gear", condition=f"user_id={user_id}"):
                await ctx.send("User hasn\'t created a gearset.")
                return

            db.delete(table="gear", condition=f"user_id={user_id}")
            await ctx.send("User has been deleted.")
    
    
    @gear.group(pass_context=True, invoke_without_command=True)
    async def help(self, ctx: Context):
        async with ctx.channel.typing():
            await ctx.send(embed=self.gear_help)
        
        
    async def post_gear(self, ctx: Context, user_id: str):
        try:
            db.select(values="*", 
                      table="gear", 
                      condition=f"user_id={user_id}")
            res = db.fetchone()
            
            _, ap, aap, dp, hp, all_ap, all_aap, accuracy, dr, dr_rate, evasion, se_rate, player_class, level, planner, img = res
            """ ap, aap, dp, hp, all_ap, all_aap, accuracy, dr, dr_rate, evasion, se_rate, player_class, level, planner, img = \
            100, 100, 300, 5000, 600, 600, 800, 300, "30 %", 600, "20 %", "Striker", 63.3, "www.garmoth.com/character/asofiaf1", 1 """
            
            embed = discord.Embed(title="Gear",
                                  description=f"{ctx.author.mention}\'s gear.\n"
                                              f"```css\n"
                                              f"Class:      {player_class},\n"
                                              f"Level:      {level},\n"
                                              f"Gear Score: {self.gearscore(ap, aap, dp):.1f}\n"
                                              f"```\n"
                                              f"[Garmoth planner]({planner.replace('www.', 'https://', 1)})",
                                  color=cfg.embed_color)
            # TODO: FIX FORMATING
            embed.add_field(name="Offensive stats",
                            value="",
                            inline=False)
            embed.add_field(name=f"{'AP':^7}|{'Total':^7}",
                            value=f"{ap:^7}|{all_ap:^7}",
                            inline=True)
            embed.add_field(name=f"{'AAP':^7}|{'Total':^7}",
                            value=f"{aap:^7}|{all_aap:^7}",
                            inline=True)
            embed.add_field(name="Accuracy",
                            value=f"{accuracy}",
                            inline=True)
            embed.add_field(name="", 
                            value="")
            embed.add_field(name="Defensive stats",
                            value="",
                            inline=False)
            embed.add_field(name="DP",
                            value=f"{dp}",
                            inline=True)
            embed.add_field(name=f"{'DR':^7}|{'Rate':^7}",
                            value=f"{dr:^7}|{dr_rate:^7}",
                            inline=True)
            embed.add_field(name=f"{'Evasion':^7}|{'Rate':^7}",
                            value=f"{evasion:^7}|{se_rate:^7}",
                            inline=True)
            #embed.add_field(name="HP",
            #                value=f"{hp}",
            #                inline=True)

            if img:
                photo = discord.File(f"{cfg.gear.path}\\{user_id}.png")
                embed.set_image(url=f"attachment://{user_id}.png")
                await ctx.send(embed=embed, file=photo)
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            print(e)
    
    
    async def process_stats(self, ctx: Context, params: str) -> bool:
        if params is None: 
            return False, "No parameters have been provided."
        try:
            db.begin()
            for param in params.split(';'):
                name, value = param.split('=')
                name, value = name.strip().lower(), value.strip()
                match name:
                    case "ap"|"total_ap"|"aap"|"total_aap"|"dp"|"hp"|"accuracy":
                        if regex.int_pattern.match(value) is None:
                            db.rollback()
                            return False, f"Provided value {value} is not a number."
                        
                        db.update(values=f"{name}={value}",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                    
                    case "dr"|"evasion":
                        if regex.int_pattern.match(value) is None and regex.tripplet.match(value) is None:
                            db.rollback()
                            return False, f"Provided value {value} doesn\'t match either of valid formats."
                        
                        if regex.tripplet.match(value) is not None: 
                            melee, magic, ranged = value[1:-1].replace(' ', '').split(',')
                            value = f"({melee}, {magic}, {ranged})"
                            
                        db.update(values=f"{name}=\"{value}\"",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                    
                    case "dr_rate"|"se_rate":
                        if regex.percentage.match(value) is None:
                            db.rollback()
                            return False, f"Provided value {param} is not in valid format."
                        
                        db.update(values=f"{name}=\"{value.strip('%').strip().replace(',', '.')} %\"",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                    
                    case "class"|"level":
                        if regex.string_or_level.match(value) is None:
                            db.rollback()
                            return False, f"Provided value {param} is not in valid format."

                        db.update(values=f"{name}=\"{value}\"",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                        
                    case "plan":
                        if regex.garmoth_url.match(value) is None:
                            db.rollback()
                            return False, f"Provided url {value} doesn\'t match official garmoth.com gear build url."
                        
                        db.update(values=f"{name}=\"{value}\"",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                    
                    case "img":
                        has_gear_img = 1
                        img_path = f"{cfg.gear.path}\\{ctx.author.id}.png"
                        
                        if value in ("None", "none"):
                            has_gear_img = 0
                            utils.delete_image(img_path)
                            
                        elif bool(value):
                            img = utils.get_image_from_url(value)
                            improc.resize_and_save(img, img_path, (cfg.gear.img_width, cfg.gear.img_height))
                                
                        elif bool(ctx.message.attachments):
                            img = await utils.get_image_from_attachment(ctx.message.attachments[0])
                            improc.resize_and_save(img, img_path, (cfg.gear.img_width, cfg.gear.img_height))
                        
                        else:
                            db.rollback()
                            return False, f"Unable to process the value {value} assigned to {name}."
                        
                        db.update(values=f"{name}={has_gear_img}",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                    
                    case _:
                        db.rollback()
                        return False, f"Parameter {name} doesn\'t exist."
        except:
            db.rollback()
            return False, f"An exception has been raised while parsing provided parameters. \
                Please make sure that you\'ve used the correct syntax."
        
        db.commit()
        return True, "ok"
    
    
    def gearscore(self, ap: int, aap: int, dp: int) -> int|float:
        return (ap + aap) / 2 + dp
    
    
    def scrape_webpage_content(self, link: str) -> Any:
        driver = webdriver.Edge(executable_path=cfg.gear.webdriver_path)
        driver.set_window_size(cfg.gear.browser_window_width, 
                               cfg.gear.browser_window_height)
        driver.get(link)

        # TODO: Find a better solution to awaiting page load.
        sleep(2)
        
        content = driver.find_element_by_id("main").get_attribute("innerHTML")
        driver.quit()
        
        stats = {}
        soup = BeautifulSoup(content, features="html.parser")
        
        # ap, aap, dp
        div = soup.find(name="div", attrs="grid grid-cols-4 items-end text-center")
        p_names = div.find_all(name="p", attrs="font-bold")
        p_values = div.find_all(name="p", attrs="text-2xl font-bold")

        for _name, _value in zip(p_names, p_values):
            name = _name.get_text().strip()
            value = _value.get_text().strip()
            
            if name in cfg.gear.name_mapping.keys():
                stats[cfg.gear.name_mapping[name]] = value

        # total ap, total aap, accuracy, (melee, range, magic) dr, (melee, range, magic) evasion, hp
        table = soup.find(name="table", attrs="bg-600 relative")
        td_names = table.find_all(name="td", attrs="max-w-0 overflow-hidden text-ellipsis whitespace-nowrap pl-2 text-left")
        td_values = table.find_all(name="span", attrs={"style": "min-width: 100px;"})

        for _name, _value in zip(td_names, td_values):
            name = _name.get_text().strip()
            value = _value.get_text().strip()
            
            if name in cfg.gear.name_mapping.keys():
                stats[cfg.gear.name_mapping[name]] = value
                
        # dr_rate, se_rate
        for table in soup.find_all(name="table", attrs="bg-600 relative overflow-hidden rounded"):
            td_names = table.find_all(name="td", attrs="max-w-0 overflow-hidden text-ellipsis whitespace-nowrap pl-2 text-left")
            td_values = table.find_all(name="span", attrs={"style": "min-width: 100px;"})
            
            for _name, _value in zip(td_names, td_values):
                name = _name.get_text().strip()
                value = _value.get_text().strip()

                if name in cfg.gear.name_mapping.keys():
                    stats[cfg.gear.name_mapping[name]] = value

        # TODO: GET CLASS + LEVEL
        
        stats["dr"] = f"({stats.pop('melee_dr')}/{stats.pop('magic_dr')}/{stats.pop('ranged_dr')})"
        stats["evasion"] = f"({stats.pop('melee_eva')}/{stats.pop('magic_eva')}/{stats.pop('ranged_eva')})"
        stats["plan"] = f"\"{link}\""
        stats["gear"] = 0
        
        return stats



async def setup(client):
    await client.add_cog(Gear(client))