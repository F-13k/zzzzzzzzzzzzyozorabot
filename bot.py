import os
import json
import asyncio
import random
import datetime
import re
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
from flask import Flask
from threading import Thread

# ==========================================
# --- 💾 SYSTÈME DE SAUVEGARDE (JSON) ---
# ==========================================
DATA_FILE = "users_xp.json"

# Charger les données au démarrage
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

# Fonction pour sauvegarder les données
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

temp_voice_channels = {} # On garde ça en mémoire vive car les vocaux disparaissent au redémarrage

# ==========================================
# --- 🌐 SERVEUR WEB (KEEP ALIVE) ---
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Le méga-bot Yozora est en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# --- ⚙️ CONFIGURATION DU BOT ET INTENTS ---
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# --- 📌 IDs DE CONFIGURATION ---
# ==========================================
# --- Boosts ---
LOG_BOOST_ID = 1529971011842215937
ROLE_BOOST_ID = 1529658219054760046

# --- XP & Général ---
ALLOWED_LEVELS_CHANNEL_ID = 1529652369044803815
WELCOME_CHANNEL_ID = 1529651322733989938
SMASH_OR_PASS_CHANNEL_ID = 1529652167743508622

# --- Vocaux Temporaires ---
CREATE_VOICE_CATEGORY_ID = 1529652853541699715  
CREATE_VOICE_CHANNEL_ID = 1529704001338085376  

# --- Logs ---
LOG_SANCTIONS_ID = 1529698855526994082
LOG_CHANNELS_ID = 1529698871566143528
LOG_LEVELS_ID = 1529698890201169962
LOG_SMASH_ID = 1529698916201660579
LOG_GENERAL_ID = 1529698855526994082

# --- Recrutements ---
CATEGORY_CANDIDATURES_ID = 1529714434354974740
RESULTATS_CANDIDATURES_ID = 1529716989025845388


# ==========================================
# --- 🛠️ VUES ET MENUS INTERACTIFS ---
# ==========================================

# 1. Vue pour les Vocaux Temporaires
class VoicePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Rendre Public 🔓", style=discord.ButtonStyle.green, custom_id="voice_public_btn")
    async def make_public(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ Tu dois être connecté dans un salon vocal pour utiliser ce bouton !", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        try:
            await channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.followup.send("✅ Ton salon vocal est désormais **Public** !", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)

    @discord.ui.button(label="Rendre Privé 🔒", style=discord.ButtonStyle.red, custom_id="voice_private_btn")
    async def make_private(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ Tu dois être connecté dans un salon vocal pour utiliser ce bouton !", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        try:
            await channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.followup.send("🔒 Ton salon vocal est désormais **Privé (sur invitation)** !", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)


# 2. Vues pour le Règlement
# 2. Vues pour le Règlement
class ReglementView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="J'accepte le règlement", style=discord.ButtonStyle.green, custom_id="accept_rules")
    async def accept_callback(self, interaction: discord.Interaction, button: Button):
        role_id = 1529660423379484793 
        role = interaction.guild.get_role(role_id)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Merci ! Tu as accès au serveur.", ephemeral=True)
        else:
            await interaction.response.send_message("Erreur : Le rôle est introuvable sur le serveur.", ephemeral=True)

    @discord.ui.button(label="Utiliser le Tag 🤍", style=discord.ButtonStyle.blurple, custom_id="use_tag_rules")
    async def tag_callback(self, interaction: discord.Interaction, button: Button):
        # --- À CONFIGURER ---
        # ID du rôle donné à ceux qui portent le tag
        tag_role_id = 1234567890123456789 # <-- REMPLACE PAR L'ID DU RÔLE TAG
        
        role = interaction.guild.get_role(tag_role_id)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Merci de soutenir Yozora en portant notre tag ! 💖", ephemeral=True)
        else:
            await interaction.response.send_message("Merci pour ton soutien ! (Erreur : rôle introuvable)", ephemeral=True)


# 3. Vues pour les Tickets
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le ticket 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Fermeture du ticket dans 3 secondes...", ephemeral=True)
        await interaction.channel.delete()

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support / Aide", description="Une question ou besoin d'aide", emoji="🎫", value="support"),
            discord.SelectOption(label="Contacter les Fondateurs", description="Affaire importante", emoji="👑", value="fondateurs"),
            discord.SelectOption(label="Signaler un abus", description="Signaler un comportement grave", emoji="🛑", value="abus"),
            discord.SelectOption(label="Partenariat", description="Proposer un partenariat", emoji="🤝", value="partenariat"),
            discord.SelectOption(label="Signalement / Plainte", description="Signaler un problème", emoji="⚠️", value="plainte"),
            discord.SelectOption(label="Autre", description="Autre demande", emoji="📌", value="autre")
        ]
        super().__init__(placeholder="Choisis le sujet de ton ticket...", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        ticket_type = self.values[0]

        category_ids = {
            "support": 1529687940312072385,
            "fondateurs": 1529688368747909313,
            "abus": 1529688444102643733,
            "partenariat": 1529688545172914176,
            "plainte": 1529688646192595114,
            "autre": 1529688715339894844
        }

        target_category_id = category_ids.get(ticket_type)
        category = guild.get_channel(target_category_id) if target_category_id else None

        channel_name = f"ticket-{ticket_type}-{member.name.lower()}"
        if discord.utils.get(guild.text_channels, name=channel_name):
            await interaction.response.send_message(f"Tu as déjà un ticket ouvert de ce type.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites, topic=f"Ticket de {member.name}")
        embed = discord.Embed(
            title=f"🎫 Ticket : {ticket_type.capitalize()}",
            description=f"Bonjour {member.mention} !\nExplique ta demande, l'équipe va te répondre.",
            color=discord.Color.pink()
        )
        await ticket_channel.send(content=f"{member.mention}", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ton ticket a été créé : {ticket_channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# 4. Vues pour les Recrutements
class DecisionModal(discord.ui.Modal):
    def __init__(self, action: str, candidat_id: int, original_message: discord.Message):
        title = "Accepter la candidature" if action == "accept" else "Refuser la candidature"
        super().__init__(title=title[:45])
        self.action = action
        self.candidat_id = candidat_id
        self.original_message = original_message

        self.raison = discord.ui.TextInput(
            label="Explication / Mot du staff :",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.raison)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        candidat = guild.get_member(self.candidat_id)
        mention = candidat.mention if candidat else f"<@{self.candidat_id}>"
        result_channel = guild.get_channel(RESULTATS_CANDIDATURES_ID)
        
        if self.action == "accept":
            embed = discord.Embed(title="🎉 Candidature Acceptée !", description=f"Bien joué {mention} !\n\n**Mot du staff :**\n{self.raison.value}", color=discord.Color.green())
        else:
            embed = discord.Embed(title="🥀 Retour sur ta candidature", description=f"Bonjour {mention},\nTu as été **refusé(e)**.\n\n**Raison :**\n{self.raison.value}", color=discord.Color.red())
            
        if result_channel:
            await result_channel.send(content=mention, embed=embed)
        
        await self.original_message.edit(content=f"✅ Décision envoyée par {interaction.user.mention}.", view=None)
        await interaction.followup.send("La décision a bien été envoyée !", ephemeral=True)

class DecisionCandidatureView(discord.ui.View):
    def __init__(self, candidat_id: int = None):
        super().__init__(timeout=None)
        self.candidat_id = candidat_id

    @discord.ui.button(label="Accepter ✅", style=discord.ButtonStyle.green, custom_id="candidature_accept_btn")
    async def btn_accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
            return
        candidat_id = self.candidat_id
        if not candidat_id:
            try:
                match = re.search(r'`(\d{17,20})`', interaction.message.embeds[0].description)
                if match: candidat_id = int(match.group(1))
            except: pass
        await interaction.response.send_modal(DecisionModal("accept", candidat_id, interaction.message))

    @discord.ui.button(label="Refuser ❌", style=discord.ButtonStyle.red, custom_id="candidature_reject_btn")
    async def btn_reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
            return
        candidat_id = self.candidat_id
        if not candidat_id:
            try:
                match = re.search(r'`(\d{17,20})`', interaction.message.embeds[0].description)
                if match: candidat_id = int(match.group(1))
            except: pass
        await interaction.response.send_modal(DecisionModal("reject", candidat_id, interaction.message))

class CandidatureModal(discord.ui.Modal, title="Formulaire de Recrutement"):
    poste = discord.ui.TextInput(label="Poste souhaité", style=discord.TextStyle.short)
    age = discord.ui.TextInput(label="Ton âge", style=discord.TextStyle.short, max_length=10)
    motivations = discord.ui.TextInput(label="Tes motivations", style=discord.TextStyle.paragraph)
    experience = discord.ui.TextInput(label="Ton expérience", style=discord.TextStyle.paragraph)
    dispo = discord.ui.TextInput(label="Tes disponibilités", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Ta candidature a été envoyée !", ephemeral=True)
        embed = discord.Embed(title=f"📝 Nouvelle Candidature : {self.poste.value}", description=f"**Candidat :** {interaction.user.mention}\n**ID :** `{interaction.user.id}`", color=discord.Color.purple())
        embed.add_field(name="Âge", value=self.age.value, inline=False)
        embed.add_field(name="Motivations", value=self.motivations.value, inline=False)
        embed.add_field(name="Expérience", value=self.experience.value, inline=False)
        embed.add_field(name="Disponibilités", value=self.dispo.value, inline=False)

        category = interaction.guild.get_channel(CATEGORY_CANDIDATURES_ID)
        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            if category:
                ticket_channel = await interaction.guild.create_text_channel(name=f"candidature-{interaction.user.name}", category=category, overwrites=overwrites)
            else:
                ticket_channel = await interaction.guild.create_text_channel(name=f"candidature-{interaction.user.name}", overwrites=overwrites)
            await ticket_channel.send(content=f"Candidature de {interaction.user.mention}", embed=embed, view=DecisionCandidatureView(candidat_id=interaction.user.id))
        except:
            await interaction.channel.send(embed=embed)

class CandidatureView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Postuler pour le Staff", style=discord.ButtonStyle.blurple, custom_id="btn_postuler_staff")
    async def btn_postuler(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CandidatureModal())


# ==========================================
# --- 🚀 ÉVÉNEMENTS GLOBAUX ---
# ==========================================

@bot.event
async def on_ready():
    print(f"🚀 Méga-Bot connecté en tant que {bot.user.name} !")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name="Boost le serveur ! 💖"))
    
    # Enregistrement de TOUTES les vues interactives pour la persistance
    bot.add_view(VoicePanelView())
    bot.add_view(CandidatureView())
    bot.add_view(DecisionCandidatureView())
    bot.add_view(ReglementView())
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(StartGiveawayView())
    bot.add_view(GiveawayView())
    
    if not voice_xp_loop.is_running():
        voice_xp_loop.start()

# --- Détection de Boost ---
@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        role = after.guild.get_role(ROLE_BOOST_ID)
        if role:
            try: await after.add_roles(role)
            except: pass
        channel = after.guild.get_channel(LOG_BOOST_ID)
        if channel:
            embed = discord.Embed(
                title="🚀 NOUVEAU BOOST DE SERVEUR !",
                description=f"Un immense merci à {after.mention} pour avoir boosté **{after.guild.name}** ! 💖✨",
                color=discord.Color.from_rgb(255, 110, 199)
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(content=after.mention, embed=embed)

# --- Rôle Automatique & Join/Leave & Logs ---
AUTO_ROLE_ID = 1529660423379484793

@bot.event
async def on_member_join(member):
    # 1. Attribuer le rôle automatique dès l'arrivée
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"Impossible d'ajouter l'autorole : {e}")

    # 2. Message de bienvenue dans le salon dédié
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="✨ Bienvenue !", description=f"Salut {member.mention} ! Bienvenue sur Yozora 🌸", color=discord.Color.pink())
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)
        
    # 3. Logs de l'arrivée
    logs = member.guild.get_channel(LOG_GENERAL_ID)
    if logs:
        await logs.send(embed=discord.Embed(title="📥 Nouveau membre", description=f"{member.mention} a rejoint.", color=discord.Color.green()))

@bot.event
async def on_member_remove(member):
    logs = member.guild.get_channel(LOG_GENERAL_ID)
    if logs:
        await logs.send(embed=discord.Embed(title="📤 Départ", description=f"{member.mention} a quitté.", color=discord.Color.red()))

@bot.event
async def on_member_ban(guild, user):
    logs = guild.get_channel(LOG_SANCTIONS_ID)
    if logs:
        await logs.send(embed=discord.Embed(title="🔨 Banni", description=f"{user.mention}", color=discord.Color.dark_red()))

@bot.event
async def on_member_unban(guild, user):
    logs = guild.get_channel(LOG_SANCTIONS_ID)
    if logs:
        await logs.send(embed=discord.Embed(title="🔓 Débanni", description=f"{user.mention}", color=discord.Color.green()))

@bot.event
async def on_guild_channel_update(before, after):
    logs = after.guild.get_channel(LOG_CHANNELS_ID)
    if logs:
        await logs.send(embed=discord.Embed(title="🛠️ Salon modifié", description=f"**{after.name}** modifié.", color=discord.Color.blue()))

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild: return
    logs = message.guild.get_channel(LOG_GENERAL_ID)
    if logs:
        await logs.send(embed=discord.Embed(title="🗑️ Message supprimé", description=f"**Auteur :** {message.author.mention}\n**Contenu :**\n{message.content}", color=discord.Color.orange()))

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild or before.content == after.content: return
    logs = before.guild.get_channel(LOG_GENERAL_ID)
    if logs:
        await logs.send(embed=discord.Embed(title="✏️ Message modifié", description=f"**Auteur :** {before.author.mention}\n**Avant :**\n{before.content}\n**Après :**\n{after.content}", color=discord.Color.blue()))

# --- Vocaux Temporaires ---
@bot.event
async def on_voice_state_update(member, before, after):
    category = member.guild.get_channel(CREATE_VOICE_CATEGORY_ID)
    if after.channel and after.channel.id == CREATE_VOICE_CHANNEL_ID:
        guild = member.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, speak=True),
            member: discord.PermissionOverwrite(manage_channels=True, connect=True, move_members=True)
        }
        new_voice = await guild.create_voice_channel(name=f"🔊│Salon de {member.name}", category=category, overwrites=overwrites)
        temp_voice_channels[new_voice.id] = member.id
        try: await member.move_to(new_voice)
        except: pass
        try:
            embed = discord.Embed(title="🎙️ Ton Salon Vocal", description="Gère ton salon avec les boutons :", color=discord.Color.purple())
            await member.send(embed=embed, view=VoicePanelView())
        except: pass

    if before.channel and before.channel.id in temp_voice_channels:
        if len(before.channel.members) == 0:
            try:
                temp_voice_channels.pop(before.channel.id, None)
                await before.channel.delete(reason="Vide.")
            except: pass

# --- Smash or Pass & XP Messages ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    if message.channel.id == SMASH_OR_PASS_CHANNEL_ID and (message.attachments or message.embeds):
        try:
            thread = await message.create_thread(name=f"Smash or Pass - {message.author.name}"[:100], auto_archive_duration=1440)
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            await thread.send(f"🔥 Nouveau post de {message.author.mention} !")
            logs = message.guild.get_channel(LOG_SMASH_ID)
            if logs: await logs.send(embed=discord.Embed(title="📸 Nouveau Smash or Pass", description=f"Par {message.author.mention}.", color=discord.Color.purple()))
        except: pass

    await add_xp(message.author, message.guild, 15, is_voice=False)
    await bot.process_commands(message)


# ==========================================
# --- 📈 SYSTÈME D'XP ET NIVEAUX ---
# ==========================================

def xp_for_level(level):
    return level * 100

async def add_xp(member, guild, xp_amount, is_voice=False):
    if member.bot: return
    user_id = str(member.id) # On convertit l'ID en texte pour le JSON
    
    if user_id not in user_data: 
        user_data[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_minutes": 0}
    
    if is_voice: 
        user_data[user_id]["voice_minutes"] += 1
    else: 
        user_data[user_id]["messages"] += 1

    user_data[user_id]["xp"] += xp_amount
    req_xp = xp_for_level(user_data[user_id]["level"])

    if user_data[user_id]["xp"] >= req_xp:
        user_data[user_id]["xp"] -= req_xp
        user_data[user_id]["level"] += 1
        new_level = user_data[user_id]["level"]
        try: await member.send(f"GG ! Tu es passé **niveau {new_level}** !")
        except: pass
        
        logs = guild.get_channel(LOG_LEVELS_ID)
        if logs: await logs.send(f"📈 **{member.mention}** est passé **niveau {new_level}** !")

        role_rewards = {5: 1529659390351638588, 15: 1529659496207483013, 25: 1529659103306055812, 50: 1529658823416090814}
        if new_level in role_rewards:
            role = guild.get_role(role_rewards[new_level])
            if role: await member.add_roles(role)
            
    # On sauvegarde après chaque modification !
    save_data()

@tasks.loop(minutes=1)
async def voice_xp_loop():
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            valid_members = [m for m in channel.members if not m.bot and not m.voice.self_deaf]
            if len(valid_members) >= 2:
                for member in valid_members:
                    await add_xp(member, guild, 10, is_voice=True)

@bot.command(name="levels", aliases=["level", "lvl", "rang"])
async def levels(ctx, member: discord.Member = None):
    if ctx.channel.id != ALLOWED_LEVELS_CHANNEL_ID:
        target = ctx.guild.get_channel(ALLOWED_LEVELS_CHANNEL_ID)
        await ctx.send(f"❌ Commande réservée au salon {target.mention if target else 'dédié'} !", delete_after=5)
        return
    t = member or ctx.author
    user_id = str(t.id) # Conversion ici aussi
    
    if user_id not in user_data: 
        user_data[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_minutes": 0}
        
    data = user_data[user_id]
    embed = discord.Embed(title=f"📊 Stats de {t.name}", description=f"**Niveau :** {data['level']}\n**XP :** {data['xp']} / {xp_for_level(data['level'])}\n**Messages :** {data['messages']}\n**Temps Vocal :** {data['voice_minutes']} min", color=discord.Color.gold())
    embed.set_thumbnail(url=t.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="givelevelyozora")
@commands.has_permissions(administrator=True)
async def givelevelyozora(ctx, member: discord.Member, levels_to_add: int):
    user_id = str(member.id) # Conversion en texte
    
    if user_id not in user_data: 
        user_data[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_minutes": 0}
    
    user_data[user_id]["level"] += levels_to_add
    new_level = user_data[user_id]["level"]
    
    role_rewards = {5: 1529659390351638588, 15: 1529659496207483013, 25: 1529659103306055812, 50: 1529658823416090814}
    roles_added = []
    
    for req_level, role_id in role_rewards.items():
        if new_level >= req_level:
            role = ctx.guild.get_role(role_id)
            if role and role not in member.roles:
                await member.add_roles(role)
                roles_added.append(role.mention)
    
    # L'indentation est corrigée ici (4 espaces avant save_data)
    save_data() 
    
    # Création du message de confirmation (Une seule fois !)
    description = f"**{levels_to_add}** niveaux ajoutés à {member.mention}.\nIl est maintenant **niveau {new_level}** !"
    if roles_added:
        description += f"\n\n🎉 **Rôles débloqués :** {', '.join(roles_added)}"

    embed = discord.Embed(title="🎁 Niveaux Ajoutés", description=description, color=discord.Color.green())
    await ctx.send(embed=embed)


# ==========================================
# --- 🛡️ COMMANDES MODÉRATION ET SETUP ---
# ==========================================

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, user_id: int, *, reason="Aucune raison"):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f"✅ {user.mention} banni.")
    except Exception as e: await ctx.send(f"❌ Erreur : {e}")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ {user.name} débanni.")
    except Exception as e: await ctx.send(f"❌ Erreur : {e}")

@bot.command(name="exclure")
@commands.has_permissions(kick_members=True)
async def exclure(ctx, user_id: int, *, reason="Aucune raison"):
    try:
        member = await ctx.guild.fetch_member(user_id)
        await member.kick(reason=reason)
        await ctx.send(f"✅ {member.mention} expulsé.")
    except Exception as e: await ctx.send(f"❌ Erreur : {e}")

@bot.command(name="mute")
@commands.has_permissions(moderate_members=True)
async def mute(ctx, user_id: int, minutes: int, *, reason="Aucune raison"):
    try:
        member = await ctx.guild.fetch_member(user_id)
        await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=minutes), reason=reason)
        await ctx.send(f"✅ {member.mention} muté pour {minutes} min.")
    except Exception as e: await ctx.send(f"❌ Erreur : {e}")

@bot.command(name="unmute")
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, user_id: int):
    try:
        member = await ctx.guild.fetch_member(user_id)
        await member.timeout(None)
        await ctx.send(f"✅ Mute retiré pour {member.mention}.")
    except Exception as e: await ctx.send(f"❌ Erreur : {e}")

@ban.error
@unban.error
@exclure.error
@mute.error
@unmute.error
async def mod_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Tu n'as pas les permissions !", delete_after=5)

@bot.command(name="setup_recrutement")
@commands.has_permissions(administrator=True)
async def setup_recrutement(ctx):
    embed = discord.Embed(title="🌸 Recrutements Ouverts !", description="👉 Clique sur le bouton pour remplir le formulaire !", color=discord.Color.pink())
    await ctx.send(embed=embed, view=CandidatureView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def createreglement(ctx):
    reglement_texte = (
        "Bienvenue sur Yozora ! Pour que notre communauté reste un espace chaleureux, sécurisé et agréable pour tout le monde, nous vous demandons de lire et de respecter les règles ci-dessous.\n\n"
        "**🛡️ Section 1 : Le Respect d'Autrui**\n"
        "• **Courtoisie obligatoire :** Le respect mutuel est la base de Yozora. Aucune insulte, attaque personnelle, harcèlement, sexisme, racisme ou discrimination ne sera tolérée.\n"
        "• **Tolérance zéro :** Les propos haineux, menaces ou incitations à la violence entraîneront un bannissement immédiat et définitif du serveur.\n"
        "• **Vie privée :** Il est strictement interdit de divulguer des informations personnelles (doxxing) sans accord explicite.\n\n"
        "**💬 Section 2 : Les Salons et la Communication**\n"
        "• **Bon salon, bon sujet :** Veillez à poster vos messages dans les salons appropriés.\n"
        "• **Anti-spam :** Le spam, le flood, l'utilisation excessive de majuscules (caps lock) ou de caractères spéciaux sont interdits.\n"
        "• **Contenus inappropriés (NSFW) :** Yozora est un espace tout public. Aucun contenu à caractère pornographique, gore, choquant ou violent n'est toléré.\n\n"
        "**🔗 Section 3 : Publicité et Liens**\n"
        "• **Publicité non autorisée :** Il est interdit de faire de la publicité pour d'autres serveurs Discord ou sites en public ou en message privé (MP).\n"
        "• **Partenariats :** Veuillez contacter directement la modération ou les fondateurs.\n\n"
        "**🔨 Section 4 : Modération et Sanctions**\n"
        "• **Décision des modérateurs :** L'équipe de Yozora est là pour veiller au bon fonctionnement du serveur. Leurs décisions sont finales.\n"
        "• **Sanctions progressives :** En cas de non-respect, vous risquez : Avertissement ➔ Mute temporaire ➔ Kick ou Ban définitif.\n\n"
        "*👉 En cliquant sur le bouton d'acceptation ci-dessous, vous certifiez avoir lu, compris et accepté de respecter l'intégralité de ce règlement sur Yozora.*"
    )

    embed = discord.Embed(
        title="🌸 RÈGLEMENT OFFICIEL DE YOZORA 🌸", 
        description=reglement_texte, 
        color=discord.Color.pink()
    )

    await ctx.send(embed=embed, view=ReglementView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def createticket(ctx):
    embed = discord.Embed(title="🎫 Centre de Support", description="Sélectionne la catégorie dans le menu ci-dessous.", color=discord.Color.pink())
    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete()


# ==========================================
# --- 🎁 SYSTÈME DE GIVEAWAY ---
# ==========================================

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()

    @discord.ui.button(label="🎉 Participer", style=discord.ButtonStyle.green, custom_id="gw_join_btn")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            self.participants.remove(interaction.user.id)
            await interaction.response.send_message("❌ Tu as retiré ta participation.", ephemeral=True)
        else:
            self.participants.add(interaction.user.id)
            await interaction.response.send_message("✅ Participation validée ! Bonne chance 🍀", ephemeral=True)

class GiveawayModal(discord.ui.Modal, title="Lancer un Giveaway 🎁"):
    prize = discord.ui.TextInput(label="Lot à gagner", placeholder="Ex: Nitro, Grade VIP...", style=discord.TextStyle.short, required=True)
    winners_count = discord.ui.TextInput(label="Nombre de gagnants", default="1", style=discord.TextStyle.short, required=True)
    duration = discord.ui.TextInput(label="Durée (s/m/h/d/y)", placeholder="Ex: 10m, 2h, 1d, 1y", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # 1. Analyse de la durée (supporte s, m, h, d, y)
        dur_str = self.duration.value.strip().lower()
        match = re.match(r'^(\d+)([smhdy])$', dur_str)
        if not match:
            await interaction.followup.send("❌ Format de durée invalide. Utilise s, m, h, d ou y (ex: 10m, 2h, 1d, 1y).", ephemeral=True)
            return
        
        amount, unit = int(match.group(1)), match.group(2)
        multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'y': 31536000 # 365 jours
        }
        seconds = amount * multipliers[unit]
        
        # 2. Vérification du nombre de gagnants
        try:
            winners = int(self.winners_count.value)
            if winners < 1:
                raise ValueError()
        except ValueError:
            await interaction.followup.send("❌ Le nombre de gagnants doit être un nombre entier supérieur à 0.", ephemeral=True)
            return

        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        timestamp = int(end_time.timestamp())

        # 3. Création de l'embed et de la vue
        view = GiveawayView()
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Lot :** {self.prize.value}\n**Gagnant(s) :** {winners}\n**Fin :** <t:{timestamp}:R> (<t:{timestamp}:F>)\n\nClique sur le bouton **🎉 Participer** ci-dessous pour tenter ta chance !",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Lancé par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        msg = await interaction.channel.send(embed=embed, view=view)
        await interaction.followup.send("✅ Giveaway lancé avec succès !", ephemeral=True)

        # 4. Tâche de fond pour clôturer le giveaway
        async def end_giveaway():
            await asyncio.sleep(seconds)
            
            if not view.participants:
                try:
                    await msg.edit(content="❌ **Giveaway annulé :** Aucun participant enregistré.", embed=None, view=None)
                except:
                    pass
                return

            actual_winners_count = min(winners, len(view.participants))
            winner_ids = random.sample(list(view.participants), actual_winners_count)
            winner_mentions = [f"<@{uid}>" for uid in winner_ids]

            end_embed = discord.Embed(
                title="🎉 GIVEAWAY TERMINÉ 🎉",
                description=f"**Lot :** {self.prize.value}\n**Gagnant(s) :** {', '.join(winner_mentions)}",
                color=discord.Color.green()
            )
            try:
                await msg.edit(embed=end_embed, view=None)
                await msg.reply(f"🎊 Félicitations {', '.join(winner_mentions)} ! Vous remportez : **{self.prize.value}** !")
            except:
                pass

        bot.loop.create_task(end_giveaway())

# Vue pour déclencher le modal de giveaway via un bouton d'administration
class StartGiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 Créer un Giveaway", style=discord.ButtonStyle.blurple, custom_id="start_gw_modal_btn")
    async def start_gw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
            return
        await interaction.response.send_modal(GiveawayModal())

@bot.command(name="setup_giveaway")
@commands.has_permissions(administrator=True)
async def setup_giveaway(ctx):
    embed = discord.Embed(title="🎁 Panneau des Giveaways", description="Clique sur le bouton ci-dessous pour lancer un nouveau giveaway sur le serveur.", color=discord.Color.pink())
    await ctx.send(embed=embed, view=StartGiveawayView())
    await ctx.message.delete()


# ==========================================
# --- 🧰 COMMANDES UTILITAIRES ---
# ==========================================

# 1. Latence du bot
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Pong !", description=f"La latence du bot est de **{latency} ms**.", color=discord.Color.green())
    await ctx.send(embed=embed)

# 2. Nettoyer / Supprimer des messages en masse
@bot.command(name="clear", aliases=["purge"])
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("❌ Spécifie un nombre de messages supérieur à 0.", delete_after=5)
        return
    try:
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"🧹 **{len(deleted)}** messages ont été supprimés avec succès !", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la suppression : {e}", delete_after=5)

# 3. Informations sur le serveur
@bot.command(name="serverinfo", aliases=["si", "serveur"])
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Informations sur {guild.name}", color=discord.Color.purple())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 Propriétaire", value=guild.owner.mention if guild.owner else "Inconnu", inline=True)
    embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)
    embed.add_field(name="📅 Création", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name="💬 Salons", value=f"Textuels : {len(guild.text_channels)} | Vocaux : {len(guild.voice_channels)}", inline=True)
    embed.add_field(name="🛡️ Rôles", value=len(guild.roles), inline=True)
    await ctx.send(embed=embed)

# 4. Informations sur un membre (ou soi-même)
@bot.command(name="userinfo", aliases=["ui", "whois"])
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
    roles_str = ", ".join(roles) if roles else "Aucun rôle"
    
    embed = discord.Embed(title=f"👤 Informations de {member.name}", color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📅 Arrivée sur le serveur", value=f"<t:{int(member.joined_at.timestamp())}:D>" if member.joined_at else "Inconnu", inline=True)
    embed.add_field(name="🎂 Inscription Discord", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name=f"🎭 Rôles ({len(roles)})", value=roles_str, inline=False)
    await ctx.send(embed=embed)

# 5. Afficher l'avatar d'un utilisateur
@bot.command(name="avatar", aliases=["av"])
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    avatar_url = str(member.display_avatar.url)
    
    embed = discord.Embed(
        title=f"🖼️ Avatar de {member.name}", 
        color=discord.Color.from_rgb(255, 110, 199)
    )
    embed.set_image(url=avatar_url)
    embed.set_footer(text=f"Demandé par {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# 6. Créer un sondage propre et esthétique
@bot.command(name="poll", aliases=["sondage"])
@commands.has_permissions(manage_messages=True)
async def poll(ctx, *, question):
    try:
        await ctx.message.delete()
    except:
        pass
        
    embed = discord.Embed(
        title="📊 **Sondage officiel**",
        description=f"\n> **{question}**\n\n",
        color=discord.Color.from_rgb(138, 43, 226) # Violet élégant
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text="Réagissez ci-dessous pour voter ! ✨")
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

# ==========================================
# --- 🚀 LANCEMENT DU BOT (VITAL POUR RENDER) ---
# ==========================================

keep_alive() # Lance le faux serveur web pour que Render ne coupe pas le bot

# On récupère le token secret configuré dans l'onglet Environment de Render
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("❌ ERREUR FATALE : Le token Discord est introuvable. As-tu bien configuré DISCORD_TOKEN sur Render ?")
else:
    bot.run(TOKEN)
