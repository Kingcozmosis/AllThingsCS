import discord
from discord.ext import commands
import re
import asyncio
import requests
from bs4 import BeautifulSoup

from gpt4all import GPT4All


# -----------------------------
# DuckDuckGo Search
# -----------------------------
def search_web(query, results=3):

    try:

        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        soup = BeautifulSoup(r.text, "html.parser")

        snippets = []

        for result in soup.find_all("a", class_="result__snippet", limit=results):
            snippets.append(result.get_text())

        return "\n".join(snippets)

    except Exception as e:
        print("Search error:", e)
        return None


# -----------------------------
# Cog
# -----------------------------
class CSSmartChatCog(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        print("Loading local GPT4All model...")

        self.model = GPT4All(
            model_name="mistral-7b-instruct-v0.1.Q4_0.gguf",
            model_path=r"C:\Users\doged\AppData\Local\nomic.ai\GPT4All"
        )

        print("Local AI ready.")

    # -----------------------------
    # Listen for mentions
    # -----------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if self.bot.user in message.mentions:

            query = re.sub(f"<@!?{self.bot.user.id}>", "", message.content).strip()

            if not query:
                await message.channel.send("Ask me something about Counter-Strike.")
                return

            thinking = await message.channel.send("💭 Searching...")

            try:

                answer = await asyncio.wait_for(self.handle_query(query), timeout=40)

            except asyncio.TimeoutError:

                answer = "That took too long to answer."

            await thinking.edit(content=f"{message.author.mention} {answer}")

    # -----------------------------
    # Check if question is CS related
    # -----------------------------
    def is_cs_question(self, question):

        prompt = f"""
Determine if the following question is related to Counter-Strike (CS2, CS:GO, esports, players, teams, tournaments, gameplay).

Respond ONLY with:
YES
or
NO

Question:
{question}

Answer:
"""

        result = self.model.generate(
            prompt,
            max_tokens=5,
            temp=0
        )

        return "yes" in result.lower()

    # -----------------------------
    # Main logic
    # -----------------------------
    async def handle_query(self, question):

        # Step 1: Check if CS question
        if not self.is_cs_question(question):

            return "I only answer Counter-Strike related questions."

        # Step 2: Web search
        context = search_web("Counter Strike " + question)

        if not context:
            context = "No reliable search results."

        # Step 3: AI summary
        prompt = f"""
You are a professional Counter-Strike esports assistant.

Answer the user's question using the search context.

Rules:
- 1 or 2 short sentences
- Be factual
- Do NOT explain reasoning
- Do NOT repeat the question
- Just give the answer

Search Context:
{context}

Question:
{question}

Answer:
"""

        response = self.model.generate(
            prompt,
            max_tokens=120,
            temp=0.2
        )

        answer = response.strip()

        # Clean weird model outputs
        answer = answer.replace("Answer:", "").strip()

        return answer


# -----------------------------
# Setup
# -----------------------------
async def setup(bot):
    await bot.add_cog(CSSmartChatCog(bot))