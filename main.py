import discord
from discord.ext import commands
from discord.ext.commands.context import Context
import secret
import config

bot = commands.Bot(command_prefix='!', description='Testing description', intents=discord.Intents.default())
config = config.Config()

@bot.event
async def on_ready():
    print(f'Logged in')

@bot.command(description='''
This sets the channel that this bot will use. If not set, the bot will simply respond in the same channel. 
The bot will still listen to all channels for commands.''')
async def setChannel(context: Context, channel: discord.TextChannel):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
    else:
        config.set(context.guild.id, config.BOT_CHANNEL, channel.id)
        await sendMessage(context, 'Bot channel successfully set')

@bot.command(description='''This sets the user role which can interact with the bot. 
If no role is set, it will default to any role with "Admin" in the name.''')
async def setRole(context: Context, role: discord.Role):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
    else:
        config.set(context.guild.id, config.ADMIN_ROLE, role.id)
        await sendMessage(context, 'Mod role successfully set')

async def sendMessage(context: Context, content: str):
    guild_id = context.guild.id
    channel = context.guild.get_channel(config.get(guild_id, config.BOT_CHANNEL))
    if channel is None:
        await context.channel.send(content)
    else:
        await channel.send(content)

def checkRole(context: Context):
    allowedRoleId = config.get(context.guild.id, config.ADMIN_ROLE)
    if allowedRoleId is None:
        for role in context.author.roles:
            if 'admin' in role.name.lower():
                return True
        return False
    else:
        allowedRole = context.guild.get_role(allowedRoleId)
        return allowedRole in context.author.roles

if __name__ == "__main__":
    bot.run(secret.TOKEN)
