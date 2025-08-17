
# -*- coding: utf-8 -*-
"""
Kisuke Bot — Prefix "¤"
Prêt pour GitHub ➜ Railway
"""
import os
import logging
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("kisuke")

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Variable d'environnement DISCORD_TOKEN manquante.")

PREFIX = os.getenv("PREFIX", "¤")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, case_insensitive=True, help_command=None)

@bot.event
async def on_ready():
    log.info("Connecté en tant que %s (%s)", bot.user, bot.user.id)
    activity = discord.Activity(type=discord.ActivityType.playing, name=f"{PREFIX}help")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply(f"Il manque un argument : `{error.param.name}`")
    if isinstance(error, commands.CheckFailure):
        return await ctx.reply("Tu n'as pas la permission pour ça.")
    log.exception("Erreur sur la commande %s: %s", ctx.command, error)
    await ctx.reply("Oups, une erreur est survenue.")

@bot.command(name="help")
async def help_cmd(ctx):
    p = PREFIX
    embed = discord.Embed(
        title="Aide — Kisuke",
        description=(
            f"Préfixe: **{p}**\n\n"
            f"**Commandes de base**\n"
            f"- `{p}ping` → Pong et latence.\n"
            f"- `{p}say <texte>` → Le bot répète ton message.\n"
            f"- `{p}about` → Infos sur le bot.\n"
        ),
        color=0x9B6B43
    )
    embed.set_footer(text="Miri • Kisuke Bot")
    await ctx.reply(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    ms = round(bot.latency * 1000)
    await ctx.reply(f"Pong! `{ms}ms`")

@bot.command(name="say")
async def say(ctx, *, text: str):
    await ctx.reply(text)

@bot.command(name="about")
async def about(ctx):
    embed = discord.Embed(
        title="Kisuke Bot",
        description="Bot Discord simple, prêt pour Railway, avec préfixe `¤`.",
        color=0x2F3136
    )
    embed.add_field(name="Préfixe", value=f"`{PREFIX}`", inline=True)
    embed.add_field(name="Python", value=f"`{os.sys.version.split()[0]}`", inline=True)
    embed.set_footer(text="Made with ❤️")
    await ctx.reply(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
