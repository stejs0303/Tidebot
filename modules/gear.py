import discord
from discord.ext import commands

import io

from PIL import Image

from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep

import utils.image_processing as improc
import utils.discord_utils as utils

from typing import Any

from config import cfg
from database import db


class Gear(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
        self.gear_help = discord.Embed(title="Gear help",
                                       colour=cfg.embed_color)
    
        # "ap"|"aap"|"dp"|"acc"|"dr"|"eva"|"hp"|"all_ap"|"all_aap"|"class"|"level"
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
            state, message = await self.process_stats(ctx, params)
            if state:
                await ctx.send("Gear has been updated.")
                await self.post_gear(ctx, ctx.author.id)
            else:
                await ctx.send(f"Error: {message}")

    
    @set.command()
    async def garmoth(self, ctx: commands.Context, link = None):
        async with ctx.channel.typing():
            if link is not None:
                if cfg.gear.url_regex.match(link) is None:
                    ctx.send(f"Provided url {link} doesn\'t match garmoth.com gear build.")
                    return
                 
            elif db.contains(table="gear", condition=f"user_id={ctx.author.id}"):
                db.select(values=f"plan",
                          table="gear",
                          condition=f"user_id={ctx.author.id}")
                link = db.fetchone()[0].strip("\"")
                
            else:
                ctx.send("You have to provide garmoth.com link or have it already set in your gear set.")
                return
        
            content = self.get_webpage_content(link, ctx.author.id)
            stats = self.parse_webpage_content(content)
            # finish updating values
            
    
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
            db.select(values="*", 
                      table="gear", 
                      condition=f"user_id={user_id}")
            res = db.fetchone()
            
            _, ap, aap, dp, health, all_ap, all_aap, accuracy, dr, dr_rate, evasion, se_rate, player_class, level, planner, _ = res
            """ ap, aap, dp, health, all_ap, all_aap, accuracy, dr, dr_rate, evasion, se_rate, player_class, level, planner = \
            100, 100, 300, 5000, 600, 600, 800, 300, 30, 600, 20, "Striker", 63.3, "" """
            
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
        if params is None: 
            return False, "No parameters have been provided."
        try:
            db.begin()
            for param in params.split(';'):
                name, value = param.split('=')
                name, value = name.strip().lower(), value.strip()
                match name:
                    case "ap"|"aap"|"dp"|"acc"|"dr"|"eva"|"hp"|"all_ap"|"all_aap"|"class"|"level":
                        if cfg.gear.num_regex.match(value) is None:
                            db.rollback()
                            return False, f"Provided value {value} is not a number."
                        
                        db.update(values=f"{name}={value}",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                        
                    case "dr_rate"|"se_rate":
                        if cfg.gear.percentage_regex.match(value) is None:
                            db.rollback()
                            return False, f"Provided value {value} is not in valid format."
                        
                        db.update(values=f"{name}={value.strip('%').replace(',', '.')}",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                        
                    case "plan":
                        if cfg.gear.url_regex.match(value) is None:
                            db.rollback()
                            return False, f"Provided url {value} doesn\'t match garmoth.com gear build."
                        
                        db.update(values=f"{name}=\"{value}\"",
                                  table="gear",
                                  condition=f"user_id={ctx.author.id}")
                    
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
    
    
    def get_webpage_content(self, link: str, user_id: int) -> Any:
        driver = webdriver.Edge(executable_path=cfg.gear.webdriver_path)
        driver.set_window_size(cfg.gear.browser_window_width, 
                               cfg.gear.browser_window_height)
        driver.get(link)
        
        """TODO: Find better solution pls.."""
        sleep(2)
        
        for button in driver.find_elements_by_class_name("ncmp__btn"):
            if button.text == "Accept":
                button.click()
        
        """TODO: Find better solution pls.."""
        sleep(1)
        
        img = Image.open(io.BytesIO(driver.get_screenshot_as_png()))
        improc.resize_and_save(img, f"{cfg.gear.path}\\{user_id}.png", 
                               (cfg.gear.img_height, cfg.gear.img_width))

        content = driver.find_element_by_id("main").get_attribute("innerHTML")
        driver.quit()
        
        return content
        
    def parse_webpage_content(content) -> dict[str, str]:
        stats = {}
        soup = BeautifulSoup(content, features="html.parser")
        
        """ap INTEGER, aap INTEGER, dp INTEGER, hp INTEGER, 
           all_ap INTEGER, all_aap INTEGER, acc INTEGER, 
           dr TEXT, dr_rate INTEGER, eva TEXT, se_rate INTEGER,
           class TEXT, level REAL, plan TEXT, gear INTEGER"""
        
        #TODO: Fix names of parameters
        
        div = soup.find(name="div", attrs="grid grid-cols-4 items-end text-center")
        p_names = div.find_all(name="p", attrs="font-bold")
        p_values = div.find_all(name="p", attrs="text-2xl font-bold")

        # ap, aap, dp, score - cfg.gear.exclude
        stats |= {name.get_text().strip(): value.get_text().strip() 
                  for name, value in zip(p_names, p_values)
                  if name.get_text().strip().lower() not in cfg.gear.exclude}

        table = soup.find(name="table", attrs="bg-600 relative")
        td_names = table.find_all(name="td", attrs="max-w-0 overflow-hidden text-ellipsis whitespace-nowrap pl-2 text-left")
        td_values = table.find_all(name="span", attrs={"style": "min-width: 100px;"})

        # total ap, total aap, accuracy, (melee, range, magic) dr, (melee, range, magic) evasion - cfg.gear.exclude
        stats |= {name.get_text().strip(): value.get_text().strip() 
                  for name, value in zip(td_names, td_values)
                  if name.get_text().strip().lower() not in cfg.gear.exclude}

        for table in soup.find_all(name="table", attrs="bg-600 relative overflow-hidden rounded"):
            td_names = table.find_all(name="td", attrs="max-w-0 overflow-hidden text-ellipsis whitespace-nowrap pl-2 text-left")
            td_values = table.find_all(name="span", attrs={"style": "min-width: 100px;"})
            
            # all in cfg.gear.include
            stats |= {name.get_text().strip(): value.get_text().strip() 
                      for name, value in zip(td_names, td_values)
                      if name.get_text().strip().lower() in cfg.gear.include}

        return stats



async def setup(client):
    await client.add_cog(Gear(client))