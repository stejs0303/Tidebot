import discord
from discord import User
from discord.ext import commands
from discord.ext.commands import Context

import io
import math
 
from PIL import Image 
from PIL import ImageDraw
from PIL.Image import Resampling

import utils.discord_utils as utils
import utils.image_processing as improc

from config import cfg
from database import db
from compiled_regex import regex


class Ranking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        self.rank_help = discord.Embed(title="Ranking Help",
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
                                 f"- to make change to multiple parameters, use a semicolon ' ; ' as a separator\n"
                                 f"- keywords are not case sensitive",
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
    async def rank(self, ctx: Context, *args):
        async with ctx.channel.typing():
            user_id = utils.get_user(ctx, args)
            try:
                user: User = await self.bot.fetch_user(user_id)
                
                if not db.contains(table="ranking", condition=f"user_id={user_id}"):
                    await ctx.send(f"Couldn't find '{user.name}' in my database.")
                    return
                
                db.select(values="*",
                          table="ranking",
                          condition=f"user_id={user_id}")
                res = db.fetchone()
                _, exp, level, bg_color, full_bar_color, progress_bar_color, text_color, bg_image = res
                
                img: Image.Image = await self.generate_image(
                    user, exp, level, bg_color, full_bar_color, progress_bar_color, text_color, bg_image)
                
                with io.BytesIO() as img_bytes:
                    img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)        
                    await ctx.channel.send(file=discord.File(img_bytes, "rank.png"))

            except Exception as e:
                print(e)


    # TODO: IMPLEMENT
    @rank.command()
    async def compare(self, ctx: Context, *args):
        async with ctx.channel.typing():
            ...
                

    @rank.command()
    async def help(self, ctx: Context):
        async with ctx.channel.typing():
            await ctx.send(embed=self.rank_help)


    @rank.command()
    async def set(self, ctx: Context, *, params: str = None):
        async with ctx.channel.typing():
            state, message = await self.process_settings(ctx, params)
            if state:
                await ctx.send("Rank settings have been updated.")
            else:
                await ctx.send(f"Error: {message}")


    @rank.command()
    async def reset(self, ctx: Context, *args):
        async with ctx.channel.typing():
            user_id = utils.get_user(ctx, args)
            try:
                if not db.contains(table="ranking", condition=f"user_id={user_id}"):
                    user: User = await self.bot.fetch_user(user_id)
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
                
                utils.delete_image(f"{cfg.ranking.path}\\{user_id}.png")
                await ctx.send("Settings have been resetted.")
                
            except Exception as e:
                print(e)
    

    async def process_settings(self, ctx: Context, params: str) -> bool:
        if params is None: 
            return False, "No parameters have been provided."
        try:
            db.begin()
            for param in params.split(';'):
                name, value = param.split('=')
                name, value = name.strip().lower(), value.strip()
                match name:
                    case "bg_color" | "full_bar_color" | "progress_bar_color" | "text_color":
                        if regex.hexa_hash.match(value):
                            color = int(f"0xFF{value[5:7]}{value[3:5]}{value[1:3]}", 16)

                        elif regex.hexa_0x.match(value):
                            color = int(f"0xFF{value[6:8]}{value[4:6]}{value[2:4]}", 16)

                        elif len(channels := value.split(',')) == 3:
                            r, g, b = channels
                            color = int(f"0xFF{hex(b)[2:]:0>2}{hex(g)[2:]:0>2}{hex(r)[2:]:0>2}", 16)

                        else:
                            db.rollback()
                            return False, f"Unable to parse the value {value} assigned to {name}"    
       
                        db.update(values=f"{name}={color}",
                                  table="ranking",
                                  condition=f"user_id={ctx.author.id}")
       
                    case "bg_image":
                        has_custom_bg = 1
                        img_path = f"{cfg.ranking.path}\\{ctx.author.id}.png"
                        
                        if value in ("None", "none"):
                            has_custom_bg = 0
                            utils.delete_image(img_path)
                            
                        elif bool(value):
                            img = utils.get_image_from_url(value)
                            improc.resize_and_save(img, img_path, (cfg.ranking.img_width, cfg.ranking.img_height))
                                
                        elif bool(ctx.message.attachments):
                            img = utils.get_image_from_attachment(ctx.message.attachments[0])
                            improc.resize_and_save(img, img_path, (cfg.ranking.img_width, cfg.ranking.img_height))
                        
                        else:
                            db.rollback()
                            return False, f"Unable to process the value {value} assigned to {name}."
                        
                        db.update(values=f"{name}={has_custom_bg}",
                                  table="ranking",
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
            

    async def generate_image(self, user: User, exp: int, level: int, 
                             bg_color: int, full_bar_color: int, progress_bar_color: int, 
                             text_color: int, bg_image: int) -> Image.Image:
        image = None
        if bool(bg_image): image = Image.open(f"{cfg.ranking.path}\\{user.id}.png")
        size = (cfg.ranking.img_width, cfg.ranking.img_height)
        image_background = improc.round_rectangle(size, cfg.ranking.bg_round_rad, bg_color)
        
        with io.BytesIO() as icon_bytes:
            await user.display_avatar.save(icon_bytes)
            icon = Image.open(icon_bytes).copy()
        size = (cfg.ranking.icon_height, cfg.ranking.icon_width)
        icon = icon.resize(size, Resampling.BICUBIC)
        icon_background = improc.round_rectangle(size, cfg.ranking.icon_round_rad, 0xFF000000)
        
        size = (math.ceil(cfg.ranking.img_width - 2 * cfg.ranking.w_offset), 
                cfg.ranking.h_offset)
        full_bar = improc.round_rectangle(size, cfg.ranking.bar_round_rad, full_bar_color)
        size = (math.ceil((cfg.ranking.img_width - 2 * cfg.ranking.w_offset) / self._max_exp_at(level) * exp), 
                cfg.ranking.h_offset)
        progress_bar = improc.round_rectangle(size, cfg.ranking.bar_round_rad, progress_bar_color)
        
        out = image_background
        write = ImageDraw.Draw(out)
        
        out.paste(image or image_background, (0, 0), image_background)
        out.paste(icon or icon_background, (cfg.ranking.w_offset, cfg.ranking.h_offset), icon_background)
        
        position = (cfg.ranking.w_offset, cfg.ranking.img_height - 2 * cfg.ranking.h_offset)
        out.paste(full_bar, position, full_bar)
        out.paste(progress_bar, position, progress_bar)
        
        position = (cfg.ranking.w_offset + cfg.ranking.h_offset + cfg.ranking.icon_width, 
                    cfg.ranking.h_offset - 17)
        write.text(position, user.display_name, font=cfg.ranking.font_name, fill=text_color)
        
        position = (cfg.ranking.w_offset + cfg.ranking.h_offset + cfg.ranking.icon_width, 
                    cfg.ranking.h_offset + 80 - 17)
        write.text(position, f"Lvl: {level}", font=cfg.ranking.font_text, fill=text_color)
        
        position = (cfg.ranking.w_offset + cfg.ranking.h_offset + cfg.ranking.icon_width, 
                    cfg.ranking.h_offset + 130 - 17)
        write.text(position, f"Exp: {exp}/{self._max_exp_at(level)}", font=cfg.ranking.font_text, fill=text_color)
        
        return out


    async def generate_comparison(users: list) -> Image.Image:
        pass

async def setup(client):
    await client.add_cog(Ranking(client))