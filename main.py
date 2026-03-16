from discord.ext import commands
import discord
from discord import app_commands
from datetime import datetime
import os

# Remplace ces valeurs par celles de ton serveur
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVICE_LOG_CHANNEL_ID = int(os.getenv("SERVICE_LOG_CHANNEL_ID"))
SERVER_LOG_CHANNEL_ID = int(os.getenv("SERVER_LOG_CHANNEL_ID"))
REQUIRED_ROLE_ID = int(os.getenv("REQUIRED_ROLE_ID"))

# Initialiser le bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Dictionnaires pour suivre qui est en service et le temps de service
on_duty = {}
service_times = {}

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# Fonction pour envoyer un log
async def send_log(channel_id: int, guild: discord.Guild, message: str):
    channel = guild.get_channel(channel_id)
    if channel:
        await channel.send(message)

# Commande slash pour commencer le service
@bot.tree.command(name="service_start", description="Commencer votre service")
async def service_start(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in on_duty:
        await interaction.response.send_message(f"{interaction.user.mention}, vous êtes déjà en service !")
    else:
        on_duty[user_id] = interaction.user.name
        if user_id not in service_times:
            service_times[user_id] = 0

        log_message = f"📝 **Prise de service** : {interaction.user.mention} a commencé son service à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        await send_log(SERVICE_LOG_CHANNEL_ID, interaction.guild, log_message)

        await interaction.response.send_message(f"{interaction.user.mention} a commencé son service. Bienvenue en service !")

# Commande slash pour terminer le service
@bot.tree.command(name="service_end", description="Terminer votre service")
async def service_end(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in on_duty:
        del on_duty[user_id]
        service_times[user_id] = service_times.get(user_id, 0) + 1

        log_message = f"📝 **Fin de service** : {interaction.user.mention} a terminé son service à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        await send_log(SERVICE_LOG_CHANNEL_ID, interaction.guild, log_message)

        await interaction.response.send_message(f"{interaction.user.mention} a terminé son service. Merci pour votre service !")
    else:
        await interaction.response.send_message(f"{interaction.user.mention}, vous n'êtes pas actuellement en service.")

# Commande slash pour lister les membres en service
@bot.tree.command(name="on_duty_list", description="Lister tous les membres actuellement en service")
async def on_duty_list(interaction: discord.Interaction):
    if on_duty:
        duty_list = "\n".join(on_duty.values())
        await interaction.response.send_message(f"**Actuellement en service :**\n{duty_list}")
    else:
        await interaction.response.send_message("Personne n'est actuellement en service.")

# Commande slash pour afficher le leaderboard
@bot.tree.command(name="leadboard", description="Afficher le leaderboard des membres les plus en service")
async def leadboard(interaction: discord.Interaction):
    required_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if required_role not in interaction.user.roles:
        await interaction.response.send_message(
            f"Vous n'avez pas la permission d'utiliser cette commande. Rôle requis : {required_role.name}", ephemeral=True
        )
        return

    sorted_members = sorted(service_times.items(), key=lambda x: x[1], reverse=True)
    if not sorted_members:
        await interaction.response.send_message("Le leaderboard est vide.")
        return

    leaderboard_message = "**Leaderboard des membres les plus en service :**\n"
    for user_id, times in sorted_members:
        member = interaction.guild.get_member(user_id)
        if member:
            leaderboard_message += f"{member.display_name} : {times} fois\n"

    await interaction.response.send_message(leaderboard_message)

# Commande slash pour kick un membre
@bot.tree.command(name="kick", description="Kick un membre du serveur")
@app_commands.describe(member="Membre à kick", reason="Raison du kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison donnée"):
    required_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if required_role not in interaction.user.roles:
        await interaction.response.send_message(
            f"Vous n'avez pas la permission d'utiliser cette commande. Rôle requis : {required_role.name}", ephemeral=True
        )
        return

    await member.kick(reason=reason)
    log_message = f"⚠️ **Kick** : {member.mention} a été kick par {interaction.user.mention} pour la raison : {reason}"
    await send_log(SERVER_LOG_CHANNEL_ID, interaction.guild, log_message)

    await interaction.response.send_message(f"{member.mention} a été kick avec succès.")

# Commande slash pour ban un membre
@bot.tree.command(name="ban", description="Ban un membre du serveur")
@app_commands.describe(member="Membre à bannir", reason="Raison du ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison donnée"):
    required_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if required_role not in interaction.user.roles:
        await interaction.response.send_message(
            f"Vous n'avez pas la permission d'utiliser cette commande. Rôle requis : {required_role.name}", ephemeral=True
        )
        return

    await member.ban(reason=reason)
    log_message = f"🚫 **Ban** : {member.mention} a été banni par {interaction.user.mention} pour la raison : {reason}"
    await send_log(SERVER_LOG_CHANNEL_ID, interaction.guild, log_message)

    await interaction.response.send_message(f"{member.mention} a été banni avec succès.")

# Commande slash pour timeout un membre
@bot.tree.command(name="timeout", description="Mettre un membre en timeout")
@app_commands.describe(member="Membre à timeout", duration="Durée du timeout (en minutes)", reason="Raison du timeout")
async def timeout(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "Aucune raison donnée"):
    required_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if required_role not in interaction.user.roles:
        await interaction.response.send_message(
            f"Vous n'avez pas la permission d'utiliser cette commande. Rôle requis : {required_role.name}", ephemeral=True
        )
        return

    await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=duration), reason=reason)
    log_message = f"⏳ **Timeout** : {member.mention} a été mis en timeout par {interaction.user.mention} pour {duration} minutes. Raison : {reason}"
    await send_log(SERVER_LOG_CHANNEL_ID, interaction.guild, log_message)

    await interaction.response.send_message(f"{member.mention} a été mis en timeout pour {duration} minutes.")

# Lancer le bot
bot.run(BOT_TOKEN)
