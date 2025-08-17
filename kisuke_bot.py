# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import json
import os
import asyncio

# ─── CONFIG ──────────────────────────────────────────────
intents = discord.Intents.all()
PREFIX = os.getenv("PREFIX", "¤")
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("⚠️ Variable d'environnement DISCORD_TOKEN manquante.")

# Un seul vocal ou plusieurs (séparés par ,)
VOICE_CHANNEL_IDS = [int(x) for x in os.getenv("VOICE_CHANNEL_IDS", "1400519979660742896").split(",")]

AUTHORIZED_ADMINS = [670301667341631490, 1359569212531675167]
BLOCKED_ADMIN_ROLE_IDS = [1400518143595778079, 1400518147097759815]

USER_WL_FILE = "whitelist_users.json"
ROLE_WL_FILE = "whitelist_roles.json"
LOCK_FILE = "lock_state.json"

# ─── UTILS ──────────────────────────────────────────────
def load_list(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_list(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

whitelisted_user_ids = load_list(USER_WL_FILE)
whitelisted_role_ids = load_list(ROLE_WL_FILE)

if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "r", encoding="utf-8") as f:
        lock_active = json.load(f).get("locked", False)
else:
    lock_active = False

def save_lock_state():
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({"locked": lock_active}, f, ensure_ascii=False, indent=2)

def is_authorized(ctx):
    return ctx.author.id in AUTHORIZED_ADMINS or ctx.author.guild_permissions.administrator

async def reply_temp(ctx, content, delay=5):
    try:
        msg = await ctx.send(content)
        await asyncio.sleep(delay)
        await msg.delete()
    except:
        pass

def is_whitelisted(member):
    return (
        member.id in whitelisted_user_ids
        or any(role.id in whitelisted_role_ids for role in member.roles)
        or member.id in AUTHORIZED_ADMINS
    )

# ─── EVENTS ──────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Bot prêt : {bot.user} | Prefix: {PREFIX}")

@bot.event
async def on_voice_state_update(member, before, after):
    if lock_active and after.channel and after.channel.id in VOICE_CHANNEL_IDS:
        if not is_whitelisted(member):
            try:
                await member.move_to(None)
                print(f"Expulsé du vocal : {member}")
            except Exception as e:
                print(f"Erreur d'expulsion : {e}")

# ─── COMMANDES ───────────────────────────────────────────
@bot.command(name="lock")
async def lock(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = True
    save_lock_state()
    await reply_temp(ctx, "🔒 Expulsion automatique activée.")

@bot.command(name="unlock")
async def unlock(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = False
    save_lock_state()
    await reply_temp(ctx, "🔓 Expulsion automatique désactivée.")

@bot.command(name="lockall")
async def lockall(ctx):
    if not is_authorized(ctx):
        return
    for channel_id in VOICE_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            continue
        await channel.edit(sync_permissions=False, overwrites={})
        await channel.set_permissions(ctx.guild.default_role, connect=False)

        for rid in BLOCKED_ADMIN_ROLE_IDS:
            role = ctx.guild.get_role(rid)
            if role:
                await channel.set_permissions(role, connect=False)

        for uid in whitelisted_user_ids.union(set(AUTHORIZED_ADMINS)):
            member = ctx.guild.get_member(uid)
            if member:
                await channel.set_permissions(member, connect=True, view_channel=True, speak=True)

        for rid in whitelisted_role_ids:
            role = ctx.guild.get_role(rid)
            if role:
                await channel.set_permissions(role, connect=True, view_channel=True, speak=True)

    await reply_temp(ctx, "🔒 Tous les salons vocaux configurés ont été verrouillés.")

@bot.command(name="unlockall")
async def unlockall(ctx):
    if not is_authorized(ctx):
        return
    for channel_id in VOICE_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if isinstance(channel, discord.VoiceChannel):
            await channel.edit(overwrites={})
    await reply_temp(ctx, "🔓 Tous les salons vocaux configurés ont été déverrouillés.")

@bot.command(name="status")
async def status(ctx):
    if not is_authorized(ctx):
        return
    msg = f"**Statut :**\n- Lock actif : {lock_active}\n- Salons surveillés : {VOICE_CHANNEL_IDS}\n- Utilisateurs WL : {len(whitelisted_user_ids)}\n- Rôles WL : {len(whitelisted_role_ids)}"
    await ctx.reply(msg)

# whitelist management (add/del user/role) — inchangé
@bot.command(name="add")
async def add(ctx, membre: discord.Member):
    if not is_authorized(ctx): return
    whitelisted_user_ids.add(membre.id)
    save_list(USER_WL_FILE, whitelisted_user_ids)
    await reply_temp(ctx, f"✅ {membre.display_name} ajouté à la whitelist.")

@bot.command(name="del")
async def delete(ctx, membre: discord.Member):
    if not is_authorized(ctx): return
    whitelisted_user_ids.discard(membre.id)
    save_list(USER_WL_FILE, whitelisted_user_ids)
    await reply_temp(ctx, f"❌ {membre.display_name} retiré de la whitelist.")

@bot.command(name="addrole")
async def addrole(ctx, role: discord.Role):
    if not is_authorized(ctx): return
    whitelisted_role_ids.add(role.id)
    save_list(ROLE_WL_FILE, whitelisted_role_ids)
    await reply_temp(ctx, f"✅ Rôle {role.name} ajouté à la whitelist.")

@bot.command(name="delrole")
async def delrole(ctx, role: discord.Role):
    if not is_authorized(ctx): return
    whitelisted_role_ids.discard(role.id)
    save_list(ROLE_WL_FILE, whitelisted_role_ids)
    await reply_temp(ctx, f"❌ Rôle {role.name} retiré de la whitelist.")

@bot.command(name="wl")
async def wl(ctx):
    if not is_authorized(ctx): return
    users = [f"- {ctx.guild.get_member(uid)}" for uid in whitelisted_user_ids]
    roles = [f"- @{ctx.guild.get_role(rid)}" for rid in whitelisted_role_ids]
    msg = "**📋 Whitelist :**\n"
    msg += "\n**Utilisateurs :**\n" + ("\n".join(users) if users else "Aucun.") + "\n"
    msg += "\n**Rôles :**\n" + ("\n".join(roles) if roles else "Aucun.")
    await ctx.reply(msg)

# ─── LANCEMENT ───────────────────────────────────────────
bot.run(TOKEN)
