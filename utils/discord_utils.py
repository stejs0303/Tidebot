from discord.ext import commands

import re

def get_user(ctx: commands.Context, args) -> str:
    return str(ctx.author.id) if not bool(args) else re.search("\d+", args[0]).group()