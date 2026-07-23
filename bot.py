import os
from threading import Thread
import discord
from flask import Flask

# --- Mini serveur web pour garder le bot éveillé ---
app = Flask("")


@app.route("/")
def home():
  return "Le bot est bien en ligne !"


def run():
  app.run(host="0.0.0.0", port=8080)


def keep_alive():
  t = Thread(target=run)
  t.start()


# --- Ton code de bot Discord normal ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
  print(f"Connecté en tant que {client.user}")


# Lancement du serveur web + du bot
keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))
