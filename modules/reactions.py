import discord
from discord import Message
from discord.ext import commands, tasks

from compiled_regex import regex


class Memes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.picked_up = False
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Reactions module is now running.")
    
    
    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author == self.bot.user:
            return
    
        if regex.emote.match(message.content) is not None:
            await self.process_emote(message)
            return
        
        await self.process_text(message)

        if len(message.attachments) > 0:
            await self.process_attachment(message)

    
    async def process_emote(self, message: Message):
        response = self.get_response_to_emote(message)

        if response is None: 
            return
        
        await message.channel.send(response)


    async def process_text(self, message: Message):
        response = self.get_response_to_text(message)
        
        if response is None:
            return
        
        await message.channel.send(response)
       
        
    async def process_attachment(self, message: Message):
        pass
            

    def get_response_to_emote(self, message: Message):
        match message.content:
            case "<:monkaPickUp:1092882133044961431>":
                if not self.picked_up:
                    return "<:monkaPickUp:1092882133044961431>"

            case "<:monkaHangUp:1092882121519022140>":
                if self.picked_up:
                    return "<:monkaHangUp:1092882121519022140>"

            case _:
                return None
    
    
    def get_response_to_text(self, message: Message):
        return None
    
    
    
async def setup(client):
    await client.add_cog(Memes(client))