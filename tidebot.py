from discord.ext import commands
import discord
import asyncio
import os

from config import cfg
from database import db

from utils.messages import process_message


_intents = discord.Intents().default()
_intents.message_content = True
_intents.dm_messages = True
_intents.guild_messages = True
    
tidebot = commands.Bot(command_prefix=cfg.prefix, 
                       intents=_intents,
                       owner_id=cfg.owner_id, 
                       help_command=None)


@tidebot.event
async def on_ready():
    print(f"{tidebot.user} is now running.")
        
        
@tidebot.event
async def on_message(message: discord.Message):
    if message.author == tidebot.user:
        return
    
    if message.content[0:len(cfg.prefix)] == cfg.prefix:
        await tidebot.process_commands(message)    
        return
    
    await process_message(message)
    
    print(f"(Tidebot) {message.author} said: '{message.content}' in {message.channel}")


@tidebot.command()
async def help(ctx: commands.Context):
    async with ctx.channel.typing():
        embed = discord.Embed(title="Tidebot help", 
                              colour=cfg.embed_color, 
                              description="- shows help commands from all loaded modules")

        if bool(tidebot.get_cog("Ranking")):
            embed.add_field(name=f"{cfg.prefix}rank help", 
                            value=f"- shows help for rank commands", 
                            inline=False)
        if bool(tidebot.get_cog("Gear")):
            embed.add_field(name=f"{cfg.prefix}gear help", 
                            value=f"- shows help for gear commands", 
                            inline=False)
            
        embed.add_field(name=f"{cfg.prefix}github",
                        value=f"- link to github",
                        inline=False)
        
        
        await ctx.send(embed=embed)


@tidebot.command()
@commands.is_owner()
async def reload(ctx: commands.Context, module: str):
    async with ctx.channel.typing():
        await tidebot.unload_extension(f"modules.{module}")
        await tidebot.load_extension(f"modules.{module}")
        await ctx.send(f"Module {module} has been reloaded.")


@tidebot.command(aliases=["close_connection"])
@commands.is_owner()
async def bot_stop(ctx: commands.Context, *args):
    
    message:str = f"{tidebot.user} going dark."
    try:
        await ctx.channel.send(message)
        print(message)
        
    except Exception as e:
        print(e); exit(1)
        
    await tidebot.close()
    

@tidebot.event
async def on_command_error(message: discord.Message, error: discord.DiscordException):
    match error:
        case commands.CommandNotFound:
            await message.reply("Sorry, I can't seem to find this command.")
        case commands.NotOwner:
            await message.reply("You do not have permission to use this command.")
        case commands.MissingRequiredArgument:
            await message.reply("Please pass in all required arguments.")
        case _:
            await message.channel.send("Something went wrong, but... <:shrug:729752332589465740>")
            print(error.with_traceback())


@tidebot.event
async def on_error(event, *args, **kwargs):
    print(type(event))
    print(event)
    message: discord.Message = args[0]
    await message.reply("You've caused an error!<:reee:778565765355405392>")

    
@tidebot.command()
async def github(ctx: commands.Context, *args):
    ctx.send("https://github.com/stejs0303/Tidebot")
    

async def run() -> None: 
    async with tidebot:
        for file in os.listdir("./modules"):
            if file.endswith(".py"): 
                await tidebot.load_extension(f"modules.{file[:-3]}")
                
        await tidebot.start(cfg.token)
    
    db.close()
    
    
asyncio.run(run())