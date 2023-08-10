import discord
from discord.ext import commands

import os
import io
import re
import requests
import math
 
from PIL import Image, ImageDraw
from PIL.Image import Resampling
from utils.image_processing import round_rectangle

from config import cfg
from database import db



class Ranking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        """ TODO: f-string doesn't allow '\' fix?"""
        self.rank_help = discord.Embed(title="Ranking help",
                                       colour=cfg.embed_color)
        self.rank_help.add_field(name=f"{cfg.prefix}rank / {cfg.prefix}rank @user",
                                 value="- generates rank summary for caller or mentioned user",
                                 inline=False)
        self.rank_help.add_field(name=f"{cfg.prefix}rank set",
                                 value=f"- allows to set custom colors and or background for user's summary\n"
                                 f"- parameters:\n"
                                 f"```\nbg_image\n"
                                 f" - accepts Image, URL and None\n\n"
                                 f"bg_color, full_bar_color, progress_bar_color, text_color\n"
                                 f" - accept r, g, b values or hex code that begins with # or 0x```\n"
                                 f"- to make change to multiple parameters, use a semicolon ' ; ' as a separator",
                                 inline=False)
        self.rank_help.add_field(name=f"{cfg.prefix}rank reset",
                                 value="- resets your rank summary to default color scheme",
                                 inline=False)
        self.rank_help.add_field(name="Example",
                                 value=f"``` {cfg.prefix}rank set bg_color = 30, 10, 60; full_bar_color = Ox3F2A41 ```",
                                 inline=False)
    
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print(f"Ranking module is now running.")
    
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user:
            return
        try:
            if not db.contains(table="ranking", condition=f"user_id={message.author.id}"): 
                self.add_user(message.author.id)    
                return
            
            db.select(values="exp, level", 
                      table="ranking", 
                      condition=f"user_id={message.author.id}")
            row = db.fetchone()
        except Exception as e:
            print(e)   
        
        exp, level = row; exp += 1
        
        if self.should_lvl_up(exp, level):
            exp = 0; level += 1
            await message.channel.send(
                f"{message.author.mention} just splashed to level {level}! Tidetastic!")
        
        db.update(values=f"exp={exp}, level={level}", 
                  table="ranking", 
                  condition=f"user_id={message.author.id}")
        db.commit()    


    @commands.group(pass_context=True, invoke_without_command=True)
    async def rank(self, ctx: commands.Context, *args):
        async with ctx.channel.typing():
            user_id = ctx.author.id if not bool(args) else re.search("\d+", args[0]).group()
            try:
                user: discord.User = await self.bot.fetch_user(user_id)
                
                if not db.contains(table="ranking", condition=f"user_id={user_id}"):
                    await ctx.send(f"Couldn't find '{user.name}' in my database.")
                    return
                
                db.select(values="*",
                          table="ranking",
                          condition=f"user_id={user_id}")
                res = db.fetchone()

                img: Image.Image = await self.generate_image(
                    user, res[1], res[2], res[3], res[4], res[5], res[6], res[7])
                
                with io.BytesIO() as img_bytes:
                    img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)        
                    await ctx.channel.send(file=discord.File(img_bytes, "rank.png"))

            except Exception as e:
                print(e)
                

    @rank.command()
    async def help(self, ctx: commands.Context):
        async with ctx.channel.typing():
            await ctx.send(embed=self.rank_help)


    @rank.command()
    async def set(self, ctx: commands.Context, *, params):
        async with ctx.channel.typing():
            if await self.process_settings(ctx, params):
                await ctx.send("Rank settings have been updated.")
            else:
                await ctx.send("Something went wrong!")


    @rank.command()
    async def reset(self, ctx: commands.Context, *args):
        async with ctx.channel.typing():
            try:
                user_id = ctx.author.id if not bool(args) else re.search("\d+", args[0]).group()
                if not db.contains(table="ranking", condition=f"user_id={user_id}"):
                    user: discord.User = await self.bot.fetch_user(user_id)
                    await ctx.send(f"Couldn't find '{user.name}' in my database.")
                    return
                
                db.update(values=f"""bg_color={cfg.ranking.default_bg_color}, 
                                     full_bar_color={cfg.ranking.default_full_bar_color}, 
                                     progress_bar_color={cfg.ranking.default_progress_bar_color},
                                     text_color={cfg.ranking.default_text_color}, 
                                     bg_image=0""",
                          table="ranking",
                          condition=f"user_id={user_id}")
                db.commit()
                
                self.delete_custom_bg(f"{cfg.ranking.path}\\bg_{user_id}.png")
                await ctx.send("Settings have been resetted.")
                
            except Exception as e:
                print(e)
    

    async def process_settings(self, ctx: commands.Context, params: str) -> bool:
        try:
            parsed = {}
            for param in params.split(';'):
                name, value = param.split('=')
                name, value = name.strip(), value.strip()
                match name:
                    case "bg_color" | "full_bar_color" | "progress_bar_color" | "text_color":
                        if value[0] == '#':
                            color = int(f"0xFF{value[5:7]}{value[3:5]}{value[1:3]}", 16)
                            
                        elif value[:2] == "0x":
                            color = int(f"0xFF{value[6:8]}{value[4:6]}{value[2:4]}", 16)
                        else:
                            r, g, b = [int(channel) for channel in value.split(',')]
                            color = int(f"0xFF{hex(b)[2:]:0>2}{hex(g)[2:]:0>2}{hex(r)[2:]:0>2}", 16)
                            
                        parsed[name] = color
       
                    case "bg_image":
                        image_background = 1
                        img_path = f"{cfg.ranking.path}\\bg_{ctx.author.id}.png"
                        
                        if value in ("None", "none"):
                            image_background = 0
                            self.delete_custom_bg(img_path)
                            
                        elif bool(value):
                            img = Image.open(requests.get(value, stream=True).raw)
                            self.resize_and_save_bg(img, img_path)
                                
                        elif bool(ctx.message.attachments):
                            file = ctx.message.attachments[0]
                            img = Image.open(io.BytesIO(await file.read()))
                            self.resize_and_save_bg(img, img_path)
                        
                        else:
                            raise Exception("Wrong value passed for bg_image.")
                        
                        parsed[name] = image_background

                    case _:
                        return False
                    
            db.update(values=f"{', '.join([f'{key}={val}' for key, val in parsed.items()])}",
                      table="ranking",
                      condition=f"user_id={ctx.author.id}")
            db.commit()
        
        except Exception as e:
            print(e.with_traceback())
            return False
        
        return True

    
    def resize_and_save_bg(self, img: Image.Image, img_path: str):
        img = img.resize((cfg.ranking.img_width, cfg.ranking.img_height), Resampling.BICUBIC)
        img.save(img_path)
    

    def delete_custom_bg(self, img_path: str):
        if(os.path.exists(img_path)):
            os.remove(img_path)
    

    def should_lvl_up(self, exp: int, level: int) -> bool:
        return exp >= self._max_exp_at(level)


    def _max_exp_at(self, level: int) -> int:
        return round(level * cfg.ranking.level_scaling * 10)


    def add_user(self, user_id: int):
        try:
            db.insert(values=f"""({user_id}, 1, 1, {cfg.ranking.default_bg_color}, 
                                  {cfg.ranking.default_full_bar_color}, 
                                  {cfg.ranking.default_progress_bar_color}, 
                                  {cfg.ranking.default_text_color}, 0)""",
                      table="ranking")
            db.commit() 
                
        except Exception as e:
            print(e)
            

    async def generate_image(self, user: discord.User, exp: int, level: int, 
                             bg_color: int, full_bar_color: int, progress_bar_color: int, 
                             text_color: int, bg_image: int) -> Image.Image:
        image = None
        if bool(bg_image):
            image = Image.open(f"{cfg.ranking.path}\\bg_{user.id}.png")
        size = (cfg.ranking.img_width, cfg.ranking.img_height)
        image_background = round_rectangle(size, cfg.ranking.bg_round_rad, bg_color)
        
        with io.BytesIO() as icon_bytes:
            await user.display_avatar.save(icon_bytes)
            icon = Image.open(icon_bytes).copy()
        size = (cfg.ranking.icon_height, cfg.ranking.icon_width)
        icon = icon.resize(size, Resampling.BICUBIC)
        icon_background = round_rectangle(size, cfg.ranking.icon_round_rad, 0xFF000000)
        
        size = (math.ceil(cfg.ranking.img_width - 2 * cfg.ranking.w_offset), cfg.ranking.h_offset)
        full_bar = round_rectangle(size, cfg.ranking.bar_round_rad, full_bar_color)
        size = (math.ceil((cfg.ranking.img_width - 2 * cfg.ranking.w_offset) / self._max_exp_at(level) * exp), cfg.ranking.h_offset)
        progress_bar = round_rectangle(size, cfg.ranking.bar_round_rad, progress_bar_color)
        
        out = image_background
        write = ImageDraw.Draw(out)
        
        out.paste(image or image_background, (0, 0), image_background)
        out.paste(icon or icon_background, (cfg.ranking.w_offset, cfg.ranking.h_offset), icon_background)
        
        position = (cfg.ranking.w_offset, cfg.ranking.img_height - 2 * cfg.ranking.h_offset)
        out.paste(full_bar, position, full_bar)
        out.paste(progress_bar, position, progress_bar)
        
        position = (cfg.ranking.w_offset + cfg.ranking.h_offset + cfg.ranking.icon_width, cfg.ranking.h_offset - 17)
        write.text(position, user.display_name, font=cfg.ranking.font_name, fill=text_color)
        
        position = (cfg.ranking.w_offset + cfg.ranking.h_offset + cfg.ranking.icon_width, cfg.ranking.h_offset + 80 - 17)
        write.text(position, f"Lvl: {level}", font=cfg.ranking.font_text, fill=text_color)
        
        position = (cfg.ranking.w_offset + cfg.ranking.h_offset + cfg.ranking.icon_width, cfg.ranking.h_offset + 130 - 17)
        write.text(position, f"Exp: {exp}/{self._max_exp_at(level)}", font=cfg.ranking.font_text, fill=text_color)
        
        return out



async def setup(client):
    await client.add_cog(Ranking(client))