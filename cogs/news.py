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


class Dust2SetupView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
        self.channel = None
        self.role = None

        # Channel selector
        channel_select = discord.ui.ChannelSelect(
            placeholder="Select news channel",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )
        channel_select.callback = self.channel_callback
        self.add_item(channel_select)

        # Role selector
        role_select = discord.ui.RoleSelect(
            placeholder="Select ping role (optional)",
            min_values=0,
            max_values=1
        )
        role_select.callback = self.role_callback
        self.add_item(role_select)

    async def channel_callback(self, interaction: discord.Interaction):

        select = interaction.data["values"][0]
        self.channel = interaction.guild.get_channel(int(select))

        await interaction.response.send_message(
            f"📢 Channel set to {self.channel.mention}",
            ephemeral=True
        )

    async def role_callback(self, interaction: discord.Interaction):

        if interaction.data["values"]:
            role_id = int(interaction.data["values"][0])
            self.role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"🔔 Role set to {self.role.mention}",
                ephemeral=True
            )
        else:
            self.role = None

            await interaction.response.send_message(
                "Role cleared.",
                ephemeral=True
            )

    @discord.ui.button(label="Enable", style=discord.ButtonStyle.green)
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not self.channel:
            await interaction.response.send_message(
                "❌ Please select a channel first.",
                ephemeral=True
            )
            return

        config = self.cog.load_config()

        config[str(interaction.guild.id)] = {
            "channel": self.channel.id,
            "role": self.role.id if self.role else None,
            "last_post": None
        }

        self.cog.save_config(config)

        msg = f"✅ Dust2 news enabled in {self.channel.mention}"

        if self.role:
            msg += f"\nRole ping: {self.role.mention}"

        await interaction.response.send_message(msg)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.red)
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):

        config = self.cog.load_config()

        if str(interaction.guild.id) in config:

            del config[str(interaction.guild.id)]
            self.cog.save_config(config)

            await interaction.response.send_message("🛑 Dust2 news disabled.")

        else:

            await interaction.response.send_message(
                "❌ Dust2 news is not enabled.",
                ephemeral=True
            )


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
    # GUI Setup Command
    # -------------------------
    @app_commands.command(name="dust2", description="Setup Dust2 news")
    async def dust2(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="Dust2.us News Setup",
            description=(
                "Use the menu below to configure Dust2 news.\n\n"
                "1️⃣ Select a **channel**\n"
                "2️⃣ Select an optional **role ping**\n"
                "3️⃣ Click **Enable**"
            ),
            color=0xff6600
        )

        embed.set_thumbnail(url=DUST2_LOGO)

        await interaction.response.send_message(
            embed=embed,
            view=Dust2SetupView(self)
        )

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