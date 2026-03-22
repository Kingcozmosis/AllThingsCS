# All Things CS

**All Things CS** is a Discord bot that brings Counter-Strike directly to your server.  
Get live matches, pro player stats, team information, Dust2 news, and official CS2 updates — all powered by **BO3.gg**.

If you have a CS related question, just **@ the bot and ask!**

---

## Features

• Live Counter-Strike match tracking  
• Pro player search and stats  
• Team roster lookup  
• Automatic Dust2.us news posts  
• Automatic CS2 update posts from Steam  
• Admin setup commands for news & updates  
• Interactive embeds and buttons  
• Rotating bot status

---

## Commands

### General Commands

| Command | Description |
|------|------|
| `/help` | View all available commands |
| `/matches` | View today's or live CS matches |
| `/player` | Search for a CS2 pro player |
| `/team` | Show a CS2 team roster |

### Admin Commands

| Command | Description |
|------|------|
| `/dust2` | Setup Dust2 news posting |
| `/dust2_test` | Test Dust2 news post |
| `/cs2updates` | Setup automatic CS2 updates |
| `/cs2updates_test` | Test CS2 update post |
| `/reload` | Reload bot commands |

---

## Powered By BO3.gg

This bot uses data powered by **BO3.gg**, a next-generation esports platform focused on competitive gaming.

https://bo3.gg

---
## Installation

### 1. Clone the repository

git clone https://github.com/Kingcozmosis/all-things-cs.git
cd all-things-cs

---

### 2. Install Python

Make sure you have **Python 3.10 or newer** installed.

Check your version:

python --version

---

### 3. Install dependencies

Install all required packages:

pip install -r requirements.txt

If you don't have a requirements.txt yet, install these:

pip install discord.py python-dotenv feedparser aiohttp beautifulsoup4 cs2api

---

### 4. Create a `.env` file

Create a file called `.env` in the root of the project.

Add your Discord bot token:

DISCORD_TOKEN=your_discord_bot_token_here

---

### 5. Start the bot

Run the bot with:

python bot.py

You should see:

Bot connected as All Things CS
Slash commands synced!

---

### 6. Invite the bot to your server

Create an invite link in the **Discord Developer Portal** and invite the bot to your server.

Recommended permissions:

• Send Messages  
• Embed Links  
• Use Slash Commands  
• Read Message History  

---

### 7. Setup features in your server

Run the setup commands (Admin only):

/dust2  
/cs2updates

These allow admins to configure:

• Dust2 news posts  
• CS2 update posts  

---

### Done!

Your **All Things CS bot** should now be running and ready to use.

Try these commands:

/help  
/matches  
/player  
/team  

You can also **@mention the bot and ask CS related questions.**
