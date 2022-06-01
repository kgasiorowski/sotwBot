import discord
from discord.ext import commands
import secret
bot = commands.Bot(command_prefix='?', description='Testing description', intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f'Logged in')

@bot.command()
async def setChannel(ctx, channel: discord.TextChannel):
    print(channel)

@bot.command()
async def setRole(ctx, modRole: discord.Role):
    print(modRole)


if __name__ == "__main__":
    bot.run(secret.TOKEN)


