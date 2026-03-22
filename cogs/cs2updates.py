import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import json
import os
import re

RSS_URL = "https://steamcommunity.com/games/CSGO/rss/"
CONFIG_FILE = "data/cs2updates_config.json"

CS2_LOGO = "https://upload.wikimedia.org/wikipedia/en/thumb/6/6c/Counter-Strike_2_cover_art.jpg/512px-Counter-Strike_2_cover_art.jpg"
CS2_BANNER = "https://cdn.akamai.steamstatic.com/apps/csgo/images/csgo_react/social/cs2.jpg"


class CS2SetupView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
        self.channel = None
        self.role = None

        # Channel select
        channel_select = discord.ui.ChannelSelect(
            placeholder="Select update channel",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )
        channel_select.callback = self.channel_callback
        self.add_item(channel_select)

        # Role select
        role_select = discord.ui.RoleSelect(
            placeholder="Select ping role (optional)",
            min_values=0,
            max_values=1
        )
        role_select.callback = self.role_callback
        self.add_item(role_select)

    async def channel_callback(self, interaction: discord.Interaction):

        channel_id = int(interaction.data["values"][0])
        self.channel = interaction.guild.get_channel(channel_id)

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

        msg = f"✅ CS2 updates enabled in {self.channel.mention}"

        if self.role:
            msg += f"\nRole ping: {self.role.mention}"

        await interaction.response.send_message(msg)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.red)
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):

        config = self.cog.load_config()

        if str(interaction.guild.id) in config:

            del config[str(interaction.guild.id)]
            self.cog.save_config(config)

            await interaction.response.send_message("🛑 CS2 updates disabled.")

        else:

            await interaction.response.send_message(
                "❌ CS2 updates are not enabled.",
                ephemeral=True
            )


class CS2UpdatesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_updates.start()

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
    @app_commands.command(
        name="cs2updates",
        description="Setup CS2 update posts"
    )
    async def cs2updates(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="CS2 Update Setup",
            description=(
                "Configure automatic CS2 update posts.\n\n"
                "1️⃣ Select a **channel**\n"
                "2️⃣ Select optional **role ping**\n"
                "3️⃣ Click **Enable**"
            ),
            color=0xff6600
        )

        embed.set_thumbnail(url=CS2_LOGO)

        await interaction.response.send_message(
            embed=embed,
            view=CS2SetupView(self)
        )

    # -------------------------
    # Clean Steam HTML
    # -------------------------
    def clean_html(self, text):

        text = re.sub("<.*?>", "", text)
        text = text.replace("[", "\n**[")
        text = text.replace("]", "]**\n")

        return text.strip()

    # -------------------------
    # Test command
    # -------------------------
    @app_commands.command(
        name="cs2updates_test",
        description="Post the latest CS2 update"
    )
    async def cs2updates_test(self, interaction: discord.Interaction):

        await interaction.response.defer()

        config = self.load_config()

        if str(interaction.guild.id) not in config:

            await interaction.followup.send(
                "❌ CS2 updates not enabled."
            )
            return

        feed = feedparser.parse(RSS_URL)

        if not feed.entries:

            await interaction.followup.send(
                "❌ Could not find a CS2 update."
            )
            return

        entry = feed.entries[0]

        update = {
            "title": entry.title,
            "link": entry.link,
            "text": self.clean_html(entry.summary)
        }

        channel = self.bot.get_channel(
            config[str(interaction.guild.id)]["channel"]
        )

        await self.send_update(channel, update, config[str(interaction.guild.id)])

        await interaction.followup.send("✅ Test update posted.")

    # -------------------------
    # Send update embed
    # -------------------------
    async def send_update(self, channel, update, guild_config):

        role_ping = ""

        if guild_config.get("role"):
            role_ping = f"<@&{guild_config['role']}>"

        embed = discord.Embed(
            title=update["title"],
            url=update["link"],
            description=update["text"],
            color=0xff6600
        )

        embed.set_thumbnail(url=CS2_LOGO)
        embed.set_image(url=CS2_BANNER)

        embed.set_footer(
            text="Source: Steam Community • All Things CS • Powered by BO3.gg"
        )

        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label="View Full Update",
                url=update["link"]
            )
        )

        await channel.send(
            content=role_ping,
            embed=embed,
            view=view
        )

    # -------------------------
    # Background checker
    # -------------------------
    @tasks.loop(minutes=5)
    async def check_updates(self):

        config = self.load_config()

        if not config:
            return

        feed = feedparser.parse(RSS_URL)

        if not feed.entries:
            return

        newest = feed.entries[0]

        update = {
            "title": newest.title,
            "link": newest.link,
            "text": self.clean_html(newest.summary)
        }

        for guild_id, guild_config in config.items():

            if guild_config.get("last_post") == newest.link:
                continue

            channel = self.bot.get_channel(guild_config["channel"])

            if not channel:
                continue

            try:

                await self.send_update(channel, update, guild_config)

                config[guild_id]["last_post"] = newest.link
                self.save_config(config)

            except Exception as e:
                print(f"CS2 update error: {e}")

    @check_updates.before_loop
    async def before_updates(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(CS2UpdatesCog(bot))