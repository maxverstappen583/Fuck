import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# ===== LOAD ENV =====
load_dotenv()
TOKEN = os.getenv("TOKEN")

# ===== FLASK KEEPALIVE =====
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()  # Start Flask server

# ===== FOOTER =====
FOOTER_TEXT = "Made by Max – A custom bot for Serial"

# ===== LOAD DATA =====
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"responders": {}, "role_words": {}}

def save_data():
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# ===== INTENTS =====
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== BOT READY =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is online as {bot.user}")

# ===== AUTORESPONDER COMMANDS =====
@bot.tree.command(name="addresponder", description="Add an autoresponder word and response")
async def addresponder(interaction: discord.Interaction, word: str, response: str):
    data["responders"][word.lower()] = response
    save_data()
    embed = discord.Embed(title="Autoresponder Added",
                          description=f"Word: `{word}`\nResponse: `{response}`",
                          color=discord.Color.green())
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="removeresponder", description="Remove an autoresponder")
async def removeresponder(interaction: discord.Interaction, word: str):
    if word.lower() in data["responders"]:
        removed = data["responders"].pop(word.lower())
        save_data()
        embed = discord.Embed(title="Autoresponder Removed",
                              description=f"Word: `{word}`\nResponse: `{removed}`",
                              color=discord.Color.red())
    else:
        embed = discord.Embed(title="Error",
                              description=f"No autoresponder found for `{word}`",
                              color=discord.Color.red())
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed)

# ===== ROLE WORD COMMANDS =====
@bot.tree.command(name="setroleword", description="Set a word that gives a role")
async def setroleword(interaction: discord.Interaction, word: str, role: discord.Role):
    data["role_words"][word.lower()] = role.id
    save_data()
    embed = discord.Embed(title="Role Word Set",
                          description=f"Word: `{word}`\nRole: {role.mention}",
                          color=discord.Color.purple())
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="removeroleword", description="Remove a word-role trigger")
async def removeroleword(interaction: discord.Interaction, word: str):
    if word.lower() in data["role_words"]:
        role_id = data["role_words"].pop(word.lower())
        role = interaction.guild.get_role(role_id)
        save_data()
        embed = discord.Embed(title="Role Word Removed",
                              description=f"Word: `{word}`\nRole: `{role}`",
                              color=discord.Color.red())
    else:
        embed = discord.Embed(title="Error",
                              description=f"No role word found for `{word}`",
                              color=discord.Color.red())
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed)

# ===== LIST COMMAND =====
def format_list_embed(guild):
    embed = discord.Embed(title="Bot Responses & Role Words", color=discord.Color.blue())
    # Autoresponders
    if data["responders"]:
        responders_desc = "\n".join([f"`{w}` → {r}" for w, r in data["responders"].items()])
    else:
        responders_desc = "No autoresponders set."
    embed.add_field(name="Autoresponders", value=responders_desc, inline=False)
    
    # Role words
    if data["role_words"]:
        role_desc_list = []
        for w, role_id in data["role_words"].items():
            role = guild.get_role(role_id)
            if role:
                role_desc_list.append(f"`{w}` → {role.mention}")
            else:
                role_desc_list.append(f"`{w}` → (Role not found)")
        role_desc = "\n".join(role_desc_list)
    else:
        role_desc = "No role words set."
    embed.add_field(name="Role Words", value=role_desc, inline=False)
    
    embed.set_footer(text=FOOTER_TEXT)
    return embed

@bot.tree.command(name="list", description="List all autoresponders and role words")
async def list_slash(interaction: discord.Interaction):
    embed = format_list_embed(interaction.guild)
    await interaction.response.send_message(embed=embed)

@bot.command(name="list")
async def list_prefix(ctx):
    embed = format_list_embed(ctx.guild)
    await ctx.send(embed=embed)

# ===== EVENT LISTENER =====
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    # Autoresponders
    for word, response in data["responders"].items():
        if word in content:
            embed = discord.Embed(description=response, color=discord.Color.orange())
            embed.set_footer(text=FOOTER_TEXT)
            await message.channel.send(embed=embed)
            break

    # Role words
    for word, role_id in data["role_words"].items():
        if word in content:
            role = message.guild.get_role(role_id)
            if role:
                await message.author.add_roles(role)
                embed = discord.Embed(description=f"Gave {message.author.mention} the role {role.mention}",
                                      color=discord.Color.green())
                embed.set_footer(text=FOOTER_TEXT)
                await message.channel.send(embed=embed)
            break

    await bot.process_commands(message)

# ===== RUN BOT =====
bot.run(TOKEN)
