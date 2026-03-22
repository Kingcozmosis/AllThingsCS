import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from services.cs2api_service import CS2Service
import asyncio


class PlayerSelect(discord.ui.Select):
    def __init__(self, players, cog):
        self.players = players
        self.cog = cog

        options = []
        for i, p in enumerate(players[:25]):  # Discord max 25 options
            real = ""
            if p.get("first_name") and p.get("last_name"):
                real = f"{p['first_name']} {p['last_name']}"
            label = p["nickname"]
            desc = real if real else "Unknown name"
            options.append(discord.SelectOption(label=label, description=desc, value=str(i)))

        super().__init__(placeholder="Select the correct player", options=options)

    async def callback(self, interaction: discord.Interaction):
        player = self.players[int(self.values[0])]
        embed, view = self.cog.build_player_embed(player)
        await interaction.response.edit_message(content=None, embed=embed, view=view)


class PlayerSelectView(discord.ui.View):
    def __init__(self, players, cog):
        super().__init__(timeout=120)
        self.add_item(PlayerSelect(players, cog))


class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs = CS2Service()

    @app_commands.command(name="player", description="Search for a CS2 pro player")
    async def player(self, interaction: discord.Interaction, name: str):
        # Loading message
        await interaction.response.send_message(f"🔎 Searching for player **{name}**...")
        loading_msg = await interaction.original_response()

        try:
            task = asyncio.create_task(self.cs.search_player(name))
            players = await asyncio.wait_for(task, timeout=10)
        except asyncio.TimeoutError:
            task.cancel()
            await loading_msg.edit(
                content="⏱ Player search timed out after **10 seconds**.\n"
                        "The player may not exist or try checking your spelling."
            )
            return

        if not players:
            await loading_msg.edit(content="❌ This player is not a pro.")
            return

        # Multiple players
        if isinstance(players, list) and len(players) > 1:
            await loading_msg.edit(
                content="Multiple players found. Select the correct one:",
                view=PlayerSelectView(players, self)
            )
            return

        # Single player (either dict or list with one element)
        player = players[0] if isinstance(players, list) else players
        embed, view = self.build_player_embed(player)
        await loading_msg.edit(content=None, embed=embed, view=view)

    def build_player_embed(self, player):
        real_name = ""
        if player.get("first_name") and player.get("last_name"):
            real_name = f"{player['first_name']} {player['last_name']}"

        title = f"{player['nickname']} — {real_name}" if real_name else player["nickname"]
        embed = discord.Embed(title=title, color=0xff6600)

        # Only show country
        country = player.get("country") or {}
        country_name = country.get("name") if isinstance(country, dict) else country
        embed.add_field(name="🌍 Country", value=country_name or "N/A", inline=True)

        # Team
        team = player.get("team") or {}
        embed.add_field(name="🏆 Team", value=team.get("name", "No Team"), inline=True)

        # Age
        age_text = "N/A"
        birth_str = player.get("birthDate")
        if birth_str:
            try:
                birth = datetime.strptime(birth_str, "%Y-%m-%d")
                today = datetime.today()
                age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                age_text = str(age)
            except:
                pass
        embed.add_field(name="🎂 Age", value=age_text, inline=True)

        # Time on team (already pre-formatted in API)
        time_on_team = player.get("stats", {}).get("time_on_team", "N/A")
        embed.add_field(name="⏱ Time on Team", value=time_on_team, inline=True)

        # Prize money
        prize_val = player.get("prize_pool")
        prize_text = f"${prize_val:,}" if prize_val else "N/A"
        embed.add_field(name="💰 Total Prize", value=prize_text, inline=True)

        # Thumbnail
        if player.get("image_url"):
            embed.set_thumbnail(url=player["image_url"])

        # Buttons
        view = discord.ui.View()
        # HLTV
        view.add_item(discord.ui.Button(label="HLTV Profile", url=f"https://www.hltv.org/search?query={player['nickname']}"))
        # Steam
        if player.get("steam_link"):
            view.add_item(discord.ui.Button(label="Steam Profile", url=player["steam_link"]))
        # BO3.gg
        if player.get("slug"):
            view.add_item(discord.ui.Button(label="BO3.gg Profile", url=f"https://bo3.gg/players/{player['slug']}"))

        embed.set_footer(text="All Things CS • Powered by BO3.gg")
        return embed, view


async def setup(bot):
    await bot.add_cog(PlayerCog(bot))