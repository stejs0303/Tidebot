from discord.ext import commands as _commands
import discord as _discord

from PIL import Image as _Image

import requests as _requests

import re as _re
import io as _io

def get_user(ctx: _commands.Context, args) -> str:
    return str(ctx.author.id) if not bool(args) else _re.search("\d+", args[0]).group()


async def get_image_from_attachment(file: _discord.Attachment) -> None:
    return _Image.open(_io.BytesIO(await file.read()))

    
def get_image_from_url(file: str) -> None:
    return _Image.open(_requests.get(file, stream=True).raw)
    
