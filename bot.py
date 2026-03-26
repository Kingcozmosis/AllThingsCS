import discord
import os
import asyncio
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Status rotation list
statuses = [
    discord.Activity(type=discord.ActivityType.watching, name="BO3.GG For Everything CS"),
    discord.Activity(type=discord.ActivityType.watching, name="BO3.GG | /help"),
    discord.Activity(type=discord.ActivityType.watching, name="Scaning CS2 Matches"),
    discord.Activity(type=discord.ActivityType.watching, name="Reading Dust2 News"),
    discord.Activity(type=discord.ActivityType.watching, name="Checking Pro Player Stats")
]

status_index = 0


async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and file != "__init__.py":
            await bot.load_extension(f"cogs.{file[:-3]}")


# Rotating status task
@tasks.loop(seconds=30)
async def rotate_status():
    global status_index

    await bot.change_presence(activity=statuses[status_index])

    status_index += 1
    if status_index >= len(statuses):
        status_index = 0


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

    await bot.tree.sync()
    print("Slash commands synced!")

    if not rotate_status.is_running():
        rotate_status.start()


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())