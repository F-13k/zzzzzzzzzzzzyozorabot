import discord
from discord.ext import commands

# Configuration des intents (nécessaire pour voir les boosts et les membres)
intents = discord.Intents.default()
intents.members = True  # Indispensable pour détecter les boosts
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs configurés pour ton serveur
LOG_BOOST_ID = 1529651353679433728  # Salon où envoyer le message de boost
ROLE_BOOST_ID = 1529658219054760046  # Rôle à donner automatiquement au boosteur

@bot.event
async def on_ready():
    print(f"🚀 Bot de Boost connecté en tant que {bot.user.name} !")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name="Boost le serveur ! 💖"))

@bot.event
async def on_member_update(before, after):
    # Vérifie si le membre vient de booster le serveur (passage de non-boost à boost)
    if before.premium_since is None and after.premium_since is not None:
        
        # 1. Donner automatiquement le rôle boosteur
        role = after.guild.get_role(ROLE_BOOST_ID)
        if role:
            try:
                await after.add_roles(role)
            except Exception as e:
                print(f"Erreur lors de l'attribution du rôle boost : {e}")

        # 2. Envoyer le message de remerciement dans le salon configuré
        channel = after.guild.get_channel(LOG_BOOST_ID)
        if channel:
            embed = discord.Embed(
                title="🚀 NOUVEAU BOOST DE SERVEUR !",
                description=(
                    f"Un immense merci à {after.mention} pour avoir boosté le serveur **{after.guild.name}** ! 💖✨\n\n"
                    "Tu gères trop, ton soutien fait vivre la communauté et débloque de super avantages ! 🎉"
                ),
                color=discord.Color.from_rgb(255, 110, 199) # Rose Yozora
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="Yozora 🌸 • Merci pour ton boost !")
            
            await channel.send(content=after.mention, embed=embed)

# Mets ici le token de ton NOUVEAU bot de boost
bot.run("TON_NOUVEAU_TOKEN_ICI")
