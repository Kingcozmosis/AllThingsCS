import discord
from discord.ext import commands
from services.cs2api_service import CS2Service
import asyncio


class TeamCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cs2 = CS2Service()

    @discord.app_commands.command(name="team", description="Show a CS2 team roster")
    async def team(self, interaction: discord.Interaction, name: str):

        # Send loading message
        await interaction.response.send_message(f"🔎 Searching for team **{name}**...")
        loading_msg = await interaction.original_response()

        try:
            search_task = asyncio.create_task(self.cs2.search_team(name))
            team = await asyncio.wait_for(search_task, timeout=10)
        except asyncio.TimeoutError:
            search_task.cancel()
            await loading_msg.edit(
                content=(
                    "⏱ Team search timed out after **10 seconds**.\n"
                    "The team may not exist or try checking your spelling."
                )
            )
            return

        if not team:
            await loading_msg.edit(
                content=(
                    "❌ Team not found.\n"
                    "Make sure the team name is correct."
                )
            )
            return

        embed = discord.Embed(
            title=f"🏆 {team['name']}",
            description="Professional Counter-Strike Team",
            color=discord.Color.red()
        )

        # Team logo
        if team.get("logo"):
            embed.set_thumbnail(url=team["logo"])

        # Country and region
        country = team.get("country", "N/A")
        region = team.get("region", "N/A")

        embed.add_field(name="🌍 Country", value=country, inline=True)
        embed.add_field(name="🌎 Region", value=region, inline=True)

        # HLTV Rankings link
        embed.add_field(
            name="📊 Rankings",
            value="[View HLTV Rankings](https://www.hltv.org/ranking/teams)",
            inline=True
        )

        # Roster
        roster = team.get("roster", [])
        roster_text = "\n".join([f"• {p}" for p in roster]) if roster else "Roster not available."
        embed.add_field(name="👥 Current Roster", value=roster_text, inline=False)

        # Buttons
        view = discord.ui.View()
        hltv_url = f"https://www.hltv.org/search?query={team['name']}"
        view.add_item(discord.ui.Button(label="HLTV Page", url=hltv_url))
        if team.get("bo3_link"):
            view.add_item(discord.ui.Button(label="BO3.gg Page", url=team["bo3_link"]))

        embed.set_footer(text="All Things CS • Powered by BO3.gg")

        await loading_msg.edit(content=None, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(TeamCog(bot))