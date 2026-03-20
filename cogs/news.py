import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import json
import os
import aiohttp
from bs4 import BeautifulSoup

RSS_URL = "https://www.dust2.us/rss"
CONFIG_FILE = "data/news_config.json"

DUST2_LOGO = "https://www.dust2.us/dust2/img/static/dust2logo.png"


class NewsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_news.start()

    # -------------------------
    # Config
    # -------------------------
    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {}

        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    def save_config(self, data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # -------------------------
    # Enable news
    # -------------------------
    @app_commands.command(name="dust2", description="Enable Dust2 news")
    async def dust2(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role = None):

        config = self.load_config()

        config[str(interaction.guild.id)] = {
            "channel": channel.id,
            "role": role.id if role else None,
            "last_post": None
        }

        self.save_config(config)

        msg = f"✅ Dust2 news enabled in {channel.mention}"
        if role:
            msg += f"\nRole ping: {role.mention}"

        await interaction.response.send_message(msg)

    # -------------------------
    # Disable
    # -------------------------
    @app_commands.command(name="dust2_off", description="Disable Dust2 news")
    async def dust2_off(self, interaction: discord.Interaction):

        config = self.load_config()

        if str(interaction.guild.id) in config:
            del config[str(interaction.guild.id)]
            self.save_config(config)

            await interaction.response.send_message("🛑 Dust2 news disabled.")
        else:
            await interaction.response.send_message("❌ Dust2 news not enabled.")

    # -------------------------
    # Test command
    # -------------------------
    @app_commands.command(name="dust2_test", description="Test Dust2 news")
    async def dust2_test(self, interaction: discord.Interaction):

        await interaction.response.defer()

        config = self.load_config()

        if str(interaction.guild.id) not in config:
            await interaction.followup.send("❌ Dust2 news not enabled.")
            return

        feed = feedparser.parse(RSS_URL)

        if not feed.entries:
            await interaction.followup.send("❌ Could not fetch news.")
            return

        article = feed.entries[0]

        channel = self.bot.get_channel(config[str(interaction.guild.id)]["channel"])

        await self.send_article(channel, article, config[str(interaction.guild.id)])

        await interaction.followup.send("✅ Test article posted.")

    # -------------------------
    # Get article image
    # -------------------------
    async def fetch_image(self, url):

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            og = soup.find("meta", property="og:image")

            if og:
                return og["content"]

        except:
            pass

        return None

    # -------------------------
    # Send article
    # -------------------------
    async def send_article(self, channel, article, guild_config):

        role_ping = ""
        if guild_config.get("role"):
            role_ping = f"<@&{guild_config['role']}>"

        image = await self.fetch_image(article.link)

        embed = discord.Embed(
            title=article.title,
            url=article.link,
            description=article.description,
            color=0xff6600
        )

        embed.set_author(
            name="Dust2.us News",
            url="https://www.dust2.us",
            icon_url=DUST2_LOGO
        )

        if image:
            embed.set_image(url=image)

        embed.set_footer(text="Dust2.us News • All Things CS • Powered by BO3.gg")

        await channel.send(content=role_ping, embed=embed)

    # -------------------------
    # Background loop
    # -------------------------
    @tasks.loop(minutes=5)
    async def check_news(self):

        config = self.load_config()
        if not config:
            return

        feed = feedparser.parse(RSS_URL)

        if not feed.entries:
            return

        newest = feed.entries[0]

        for guild_id, guild_config in config.items():

            if guild_config.get("last_post") == newest.link:
                continue

            channel = self.bot.get_channel(guild_config["channel"])

            if not channel:
                continue

            try:

                await self.send_article(channel, newest, guild_config)

                config[guild_id]["last_post"] = newest.link
                self.save_config(config)

            except Exception as e:
                print("Dust2 error:", e)

    @check_news.before_loop
    async def before_news(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(NewsCog(bot))