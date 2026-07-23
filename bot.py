import discord

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

CHANNEL_ID = 1529651353679433728

@client.event
async def on_ready():
    print(f'Connecté en tant que {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Le bot est en ligne sur Yozora 🌸 !")

@client.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"Merci pour le boost {after.mention} ! 🌸")

client.run('TON_TOKEN_SECRET')
