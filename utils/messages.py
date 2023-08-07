import discord


async def process_message(message: discord.Message):

    content = reply(message.content)
    if content is None: return
    
    await message.channel.send(content)
   
    
def reply(content: str):
    
    match content:
        case "<:monkaPickUp:1092882133044961431>":
            return "<:monkaPickUp:1092882133044961431>"
        
        case "<:monkaHangUp:1092882121519022140>":
            return "<:monkaHangUp:1092882121519022140>"
        
        case _:
            return None