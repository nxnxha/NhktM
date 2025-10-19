
# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os, json, asyncio

# ─── INTENTS & BOT ───────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
PREFIX = os.getenv("PREFIX", ",")
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ─── CONFIG VIA ENV (avec valeurs par défaut de ta demande) ───────────────
def parse_int_list(value: str):
    out = []
    for part in str(value).replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("⚠️ DISCORD_TOKEN manquant.")

VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", "1428061918702342208"))
AUTHORIZED_ADMINS = parse_int_list(os.getenv("AUTHORIZED_ADMINS", "1163460580779245608,1359569212531675167"))
BLOCKED_ADMIN_ROLE_IDS = parse_int_list(os.getenv("BLOCKED_ADMIN_ROLE_IDS", "1400518143595778079,1400518147097759815"))

USER_WL_FILE = "whitelist_users.json"
ROLE_WL_FILE = "whitelist_roles.json"
LOCK_FILE = "lock_state.json"

# ─── PERSISTENCE ─────────────────────────────────────────
def load_set(path: str):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(int(x) for x in data)
    except Exception:
        pass
    return set()

def save_set(path: str, s: set):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(s), f, ensure_ascii=False, indent=2)

whitelisted_user_ids = load_set(USER_WL_FILE)
whitelisted_role_ids = load_set(ROLE_WL_FILE)

lock_active = False
if os.path.exists(LOCK_FILE):
    try:
        with open(LOCK_FILE, "r", encoding="utf-8") as f:
            lock_active = bool(json.load(f).get("locked", False))
    except Exception:
        lock_active = False

def save_lock_state():
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({"locked": lock_active}, f, ensure_ascii=False, indent=2)

# ─── HELPERS ────────────────────────────────────────────
def is_authorized(ctx) -> bool:
    # Seuls les IDs fournis (pas les admins généraux)
    return ctx.author.id in AUTHORIZED_ADMINS

async def reply_temp(ctx: commands.Context, content: str, delay: int = 6):
    try:
        msg = await ctx.reply(content, mention_author=False)
        await asyncio.sleep(delay)
        await msg.delete()
    except Exception:
        pass

def is_whitelisted(member: discord.Member) -> bool:
    if member.id in AUTHORIZED_ADMINS:
        return True
    if member.id in whitelisted_user_ids:
        return True
    if any(r.id in whitelisted_role_ids for r in member.roles):
        return True
    return False

def get_voice_channel(guild: discord.Guild):
    ch = guild.get_channel(VOICE_CHANNEL_ID) if guild else None
    return ch if isinstance(ch, discord.VoiceChannel) else None

async def grant_channel_access(guild: discord.Guild, *, member: discord.Member = None, role: discord.Role = None):
    channel = get_voice_channel(guild)
    if not channel: return False
    try:
        if member:
            await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(connect=True, view_channel=True, speak=True))
        if role:
            await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(connect=True, view_channel=True, speak=True))
        return True
    except Exception:
        return False

async def revoke_channel_access(guild: discord.Guild, *, member: discord.Member = None, role: discord.Role = None):
    channel = get_voice_channel(guild)
    if not channel: return False
    try:
        if member:
            await channel.set_permissions(member, overwrite=None)
        if role:
            await channel.set_permissions(role, overwrite=None)
        return True
    except Exception:
        return False

async def apply_channel_lock(guild: discord.Guild):
    """Hard lock: deny @everyone, block roles list, allow WL users/roles + admins autorisés."""
    channel = get_voice_channel(guild)
    if not channel: return False
    try:
        await channel.edit(sync_permissions=False, overwrites={})
        # Bloque @everyone
        await channel.set_permissions(guild.default_role, overwrite=discord.PermissionOverwrite(connect=False, view_channel=True))
        # Bloque explicitement des rôles admin si fournis
        for rid in BLOCKED_ADMIN_ROLE_IDS:
            role = guild.get_role(rid)
            if role:
                await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(connect=False))

        # Autorise les admins autorisés
        for uid in AUTHORIZED_ADMINS:
            m = guild.get_member(uid)
            if m:
                await channel.set_permissions(m, overwrite=discord.PermissionOverwrite(connect=True, view_channel=True, speak=True))

        # Autorise les whitelistés
        for uid in whitelisted_user_ids:
            m = guild.get_member(uid)
            if m:
                await channel.set_permissions(m, overwrite=discord.PermissionOverwrite(connect=True, view_channel=True, speak=True))

        for rid in whitelisted_role_ids:
            r = guild.get_role(rid)
            if r:
                await channel.set_permissions(r, overwrite=discord.PermissionOverwrite(connect=True, view_channel=True, speak=True))
        return True
    except Exception:
        return False

async def clear_channel_lock(guild: discord.Guild):
    ch = get_voice_channel(guild)
    if not ch: return False
    try:
        await ch.edit(overwrites={})
        return True
    except Exception:
        return False

# ─── EVENTS ──────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Kisuke prêt : {bot.user} | Prefix: {PREFIX}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"{PREFIX}help"))

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if not lock_active: return
    if after and after.channel and after.channel.id == VOICE_CHANNEL_ID:
        if not is_whitelisted(member):
            try:
                await member.move_to(None)  # nécessite Move Members
                print(f"Expulsé (non-whitelist): {member}")
            except Exception as e:
                print(f"Erreur d'expulsion: {e}")

# ─── COMMANDES ───────────────────────────────────────────
@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    if not is_authorized(ctx): return
    p = PREFIX
    msg = (
        f"**🛠️ Commandes (admins autorisés)**\n"
        f"- `{p}status` → diagnostic rapide\n"
        f"- `{p}lock` / `{p}unlock` → activer/désactiver l'expulsion auto\n"
        f"- `{p}locksalon` / `{p}unlocksalon` → verrouiller/déverrouiller via permissions\n"
        f"- `{p}add @user` / `{p}del @user` → ajouter/retirer un utilisateur WL (donne/retire l'accès salon)\n"
        f"- `{p}addrole @role` / `{p}delrole @role` → ajouter/retirer un rôle WL (donne/retire l'accès salon)\n"
        f"- `{p}wl` → afficher la whitelist\n"
    )
    await ctx.reply(msg, mention_author=False)

@bot.command()
async def status(ctx: commands.Context):
    if not is_authorized(ctx): return
    ch = get_voice_channel(ctx.guild)
    await ctx.reply(
        "**Status**\n"
        f"- Lock actif: `{lock_active}`\n"
        f"- Salon vocal cible: `{VOICE_CHANNEL_ID}` → {'OK' if ch else 'Introuvable'}\n"
        f"- Users WL: `{len(whitelisted_user_ids)}` | Roles WL: `{len(whitelisted_role_ids)}`",
        mention_author=False
    )

@bot.command()
async def lock(ctx: commands.Context):
    global lock_active
    if not is_authorized(ctx): return
    lock_active = True
    save_lock_state()
    await reply_temp(ctx, "🔒 Expulsion automatique **activée**.")

@bot.command()
async def unlock(ctx: commands.Context):
    global lock_active
    if not is_authorized(ctx): return
    lock_active = False
    save_lock_state()
    await reply_temp(ctx, "🔓 Expulsion automatique **désactivée**.")

@bot.command(name="locksalon")
async def locksalon(ctx: commands.Context):
    if not is_authorized(ctx): return
    ok = await apply_channel_lock(ctx.guild)
    await reply_temp(ctx, "🔐 Salon **verrouillé** (WL/admins autorisés)." if ok else "❌ Salon introuvable ou permissions insuffisantes.")

@bot.command(name="unlocksalon")
async def unlocksalon(ctx: commands.Context):
    if not is_authorized(ctx): return
    ok = await clear_channel_lock(ctx.guild)
    await reply_temp(ctx, "🔓 Salon vocal **déverrouillé**." if ok else "❌ Salon introuvable ou permissions insuffisantes.")

# — WL UTILISATEURS —
@bot.command(name="add")
async def add_user(ctx: commands.Context, membre: discord.Member):
    if not is_authorized(ctx): return
    whitelisted_user_ids.add(membre.id); save_set(USER_WL_FILE, whitelisted_user_ids)
    await grant_channel_access(ctx.guild, member=membre)
    await reply_temp(ctx, f"✅ `{membre}` ajouté à la whitelist et **autorisé** sur le vocal.")

@bot.command(name="del")
async def del_user(ctx: commands.Context, membre: discord.Member):
    if not is_authorized(ctx): return
    whitelisted_user_ids.discard(membre.id); save_set(USER_WL_FILE, whitelisted_user_ids)
    await revoke_channel_access(ctx.guild, member=membre)
    await reply_temp(ctx, f"❌ `{membre}` retiré de la whitelist et **accès spécifique retiré**.")

# — WL RÔLES —
@bot.command(name="addrole")
async def add_role(ctx: commands.Context, role: discord.Role):
    if not is_authorized(ctx): return
    whitelisted_role_ids.add(role.id); save_set(ROLE_WL_FILE, whitelisted_role_ids)
    await grant_channel_access(ctx.guild, role=role)
    await reply_temp(ctx, f"✅ Rôle **@{role.name}** ajouté à la whitelist et **autorisé** sur le vocal.")

@bot.command(name="delrole")
async def del_role(ctx: commands.Context, role: discord.Role):
    if not is_authorized(ctx): return
    whitelisted_role_ids.discard(role.id); save_set(ROLE_WL_FILE, whitelisted_role_ids)
    await revoke_channel_access(ctx.guild, role=role)
    await reply_temp(ctx, f"❌ Rôle **@{role.name}** retiré de la whitelist et **accès spécifique retiré**.")

@bot.command(name="wl")
async def show_wl(ctx: commands.Context):
    if not is_authorized(ctx): return
    users, roles = [], []
    for uid in sorted(whitelisted_user_ids):
        m = ctx.guild.get_member(uid)
        users.append(f"- {m} (`{uid}`)" if m else f"- ID: `{uid}`")
    for rid in sorted(whitelisted_role_ids):
        r = ctx.guild.get_role(rid)
        roles.append(f"- @{r.name} (`{rid}`)" if r else f"- ID: `{rid}`")
    msg = "**📋 Whitelist**\n"
    msg += "\n**Utilisateurs :**\n" + ("\n".join(users) if users else "Aucun.") + "\n"
    msg += "\n**Rôles :**\n" + ("\n".join(roles) if roles else "Aucun.")
    await ctx.reply(msg, mention_author=False)

# ─── RUN ─────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
