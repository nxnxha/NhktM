# -*- coding: utf-8 -*-
"""
Kisuke Bot — Prefix "¤"
Help robuste (fallback texte) + diag permissions
"""
import os
import logging
import discord
from discord.ext import commands

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("kisuke")

# ── Config ────────────────────────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Variable d'environnement DISCORD_TOKEN manquante.")

PREFIX = os.getenv("PREFIX", "¤")

# Intents : active aussi Message Content dans le portal Discord
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    case_insensitive=True,
    help_command=None
)

# ── Events ────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info("Connecté en tant que %s (%s)", bot.user, bot.user.id)
    activity = discord.Activity(type=discord.ActivityType.playing, name=f"{PREFIX}help")
    try:
        await bot.change_presence(status=discord.Status.online, activity=activity)
    except Exception as e:
        log.warning("Impossible de changer la présence: %s", e)

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        try:
            await ctx.send(f"Il manque un argument : `{error.param.name}`")
        except Exception:
            pass
        return
    if isinstance(error, commands.CheckFailure):
        try:
            await ctx.send("Tu n'as pas la permission pour ça.")
        except Exception:
            pass
        return
    log.exception("Erreur sur la commande %s: %s", getattr(ctx, "command", None), error)
    try:
        await ctx.send("Oups, une erreur est survenue.")
    except Exception:
        pass

# ── Commands ──────────────────────────────────────────────────────────────
@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    p = PREFIX
    # 1) On tente l'embed
    embed = discord.Embed(
        title="Aide — Kisuke",
        description=(
            f"Préfixe: **{p}**\n\n"
            f"**Commandes de base**\n"
            f"- `{p}ping` → Pong et latence.\n"
            f"- `{p}say <texte>` → Le bot répète ton message.\n"
            f"- `{p}about` → Infos sur le bot.\n"
            f"- `{p}diag` → Vérifie mes permissions dans ce salon.\n"
        ),
        color=0x9B6B43
    )
    embed.set_footer(text="Miri • Kisuke Bot")

    try:
        await ctx.send(embed=embed)
        return
    except Exception as e:
        log.warning("Envoi embed échoué, fallback texte. Raison: %s", e)

    # 2) Fallback texte pur (si Embed Links/Read Message History manquent, etc.)
    text = (
        f"**Aide — Kisuke**\n"
        f"Préfixe: **{p}**\n\n"
        f"**Commandes de base**\n"
        f"- `{p}ping` → Pong et latence.\n"
        f"- `{p}say <texte>` → Le bot répète ton message.\n"
        f"- `{p}about` → Infos sur le bot.\n"
        f"- `{p}diag` → Vérifie mes permissions dans ce salon.\n"
    )
    try:
        await ctx.send(text)
    except Exception as e:
        log.error("Impossible d'envoyer l'aide en texte non plus: %s", e)

@bot.command(name="ping")
async def ping(ctx: commands.Context):
    ms = round(bot.latency * 1000)
    try:
        await ctx.send(f"Pong! `{ms}ms`")
    except Exception as e:
        log.error("Impossible d'envoyer ping: %s", e)

@bot.command(name="say")
async def say(ctx: commands.Context, *, text: str):
    try:
        await ctx.send(text)
    except Exception as e:
        log.error("Impossible d'envoyer say: %s", e)

@bot.command(name="about")
async def about(ctx: commands.Context):
    embed = discord.Embed(
        title="Kisuke Bot",
        description="Bot Discord simple, prêt pour Railway, avec préfixe `¤`.",
        color=0x2F3136
    )
    embed.add_field(name="Préfixe", value=f"`{PREFIX}`", inline=True)
    embed.add_field(name="Python", value=f"`{os.sys.version.split()[0]}`", inline=True)
    embed.set_footer(text="Made with ❤️")
    try:
        await ctx.send(embed=embed)
    except Exception:
        # Fallback texte si Embed Links manquant
        await ctx.send(f"Kisuke Bot — Préfixe `{PREFIX}`")

@bot.command(name="diag")
async def diag(ctx: commands.Context):
    """Affiche les permissions importantes dans CE salon + intents."""
    perms = ctx.channel.permissions_for(ctx.guild.me)
    lines = [
        f"Send Messages: `{perms.send_messages}`",
        f"Embed Links: `{perms.embed_links}`",
        f"Read Message History: `{perms.read_message_history}`",
        f"Attach Files: `{perms.attach_files}`",
        f"View Channel: `{perms.view_channel}`",
    ]
    lines.append(f"Intents.message_content: `{bot.intents.message_content}`")
    await ctx.send("**Diag permissions**\n" + "\n".join(lines))

# ── Run ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
