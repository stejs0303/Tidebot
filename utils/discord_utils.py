import discord as _discord
from discord import Attachment as _Attachment
from discord.ext import commands as _commands
from discord.ext.commands import Context as _Context

from PIL import Image as _Image

import requests as _requests

import re as _re
import io as _io
import os as _os

def get_user(ctx: _Context, args) -> str:
    return str(ctx.author.id) if not bool(args) else _re.search("\d+", args[0]).group()


async def get_image_from_attachment(file: _Attachment) -> None:
    return _Image.open(_io.BytesIO(await file.read()))

    
def get_image_from_url(file: str) -> None:
    return _Image.open(_requests.get(file, stream=True).raw)
    

def delete_image(img_path: str) -> None:
    if(_os.path.exists(img_path)): _os.remove(img_path)
    
