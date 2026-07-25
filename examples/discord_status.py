import asyncio
import os

import discord
from discord.ext import tasks

from squadrcon import Rcon, RconConfig

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
SQUAD_HOST = os.environ.get("SQUAD_HOST", "")
SQUAD_PORT = os.environ.get("SQUAD_PORT", "27165")
SQUAD_PASS = os.environ.get("SQUAD_PASS", "")
MAX_PLAYERS = int(os.environ.get("MAX_PLAYERS", "100"))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "60"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

rcon = None


def connect_rcon():
    return Rcon(RconConfig(host=SQUAD_HOST, password=SQUAD_PASS, port=SQUAD_PORT))


def get_player_count():
    players = rcon.list_players()
    return len(players.players)


@tasks.loop(seconds=POLL_SECONDS)
async def update_status():
    global rcon
    try:
        count = await asyncio.to_thread(get_player_count)
    except Exception as exc:
        print(f"[-] failed to fetch player count: {exc}")
        try:
            rcon.close()
        except Exception:
            pass
        try:
            rcon = await asyncio.to_thread(connect_rcon)
            print("[+] reconnected to rcon")
        except Exception as reconnect_exc:
            print(f"[-] reconnect failed: {reconnect_exc}")
        return

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{count}/{MAX_PLAYERS} players",
    )
    await client.change_presence(activity=activity)
    print(f"[*] status updated: {count}/{MAX_PLAYERS} players")


@client.event
async def on_ready():
    global rcon
    print(f"[+] logged in as {client.user}")
    rcon = await asyncio.to_thread(connect_rcon)
    print("[+] connected to rcon")
    update_status.start()


if __name__ == "__main__":
    if not DISCORD_TOKEN or not SQUAD_HOST or not SQUAD_PASS:
        raise SystemExit("set DISCORD_TOKEN, SQUAD_HOST and SQUAD_PASS env vars first")
    client.run(DISCORD_TOKEN)
