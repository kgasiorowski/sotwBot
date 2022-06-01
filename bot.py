import discord
from discord.ext import commands
from discord.ext.commands.context import Context
import secret
import config
import logger

bot = commands.Bot(command_prefix='!', description='Testing description', intents=discord.Intents.default())
config = config.Config()
logger = logger.initLogger()

@bot.event
async def on_ready():
    print(f'Logged in')
    logger.info('Bot started')

@bot.command(description='''
This sets the channel that this bot will use. If not set, the bot will simply respond in the same channel. 
The bot will still listen to all channels for commands.
''')
async def setChannel(context: Context, channel: discord.TextChannel):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
        logger.info(f'User {context.author.name} tried to set the bot channel to {channel.name}')
    else:
        config.set(context.guild.id, config.BOT_CHANNEL, channel.id)
        await sendMessage(context, 'Bot channel successfully set')
        logger.info(f'User {context.author.name} successfully set the bot channel to {channel.name}')

@bot.command(description='''
This sets the user role which can interact with the bot. 
If no role is set, it will default to any role with "Admin" in the name.
''')
async def setRole(context: Context, role: discord.Role):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
        logger.info(f'User {context.author.name} tried to set the bot role to {role.name}')
    else:
        config.set(context.guild.id, config.ADMIN_ROLE, role.id)
        await sendMessage(context, 'Mod role successfully set')
        logger.info(f'User {context.author.name} successfully set the bot role to {role.name}')

@bot.command(description='''
This sets the channel that this bot will use. If not set, the bot will simply respond in the same channel. 
The bot will still listen to all channels for commands.
''')
async def setChannel(context: Context, channel: discord.TextChannel):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
        logger.info(f'User {context.author.name} tried to set the bot channel to {channel.name}')
    else:
        config.set(context.guild.id, config.BOT_CHANNEL, channel.id)
        await sendMessage(context, 'Bot channel successfully set')
        logger.info(f'User {context.author.name} successfully set the bot channel to {channel.name}')

@bot.command(description='''
Allows users to set the clan's name per discord server.
''')
async def setclanname(context: Context, clanName: str):
    await setConfigValue(context, config.CLAN_NAME, clanName)
    await sendMessage(context, 'Successfully updated clan name')

@bot.command(description='''
Retrieves the clan name for the current discord, if set.
''')
async def getclanname(context: Context):
    clanName = await getConfigValue(context, config.CLAN_NAME)
    await sendMessage(context, f'Clan Name -> {clanName if clanName is not None else "Not set"}')

@bot.command(description='''
Allows users to set the clan's sequential sotw number.
''')
async def setsotwnumber(context: Context, sotwnumber: int):
    await setConfigValue(context, config.SOTW_NUMBER, sotwnumber)
    await sendMessage(context, 'Successfully updated SOTW number')

@bot.command(description='''
Retrieves the clan name for the current discord, if set.
''')
async def getsotwnumber(context: Context):
    sotwNumber = await getConfigValue(context, config.SOTW_NUMBER)
    await sendMessage(context, f'SOTW Number -> {sotwNumber if sotwNumber is not None else "Not set"}')

async def setConfigValue(context: Context, configName: str, configValue):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
        logger.info(f'User {context.author.name} tried to set a config value: {configName} -> {configValue}')
    else:
        config.set(context.guild.id, configName, configValue)
        logger.info(f'User {context.author.name} set a configuration value: {configName} -> {configValue}')

async def getConfigValue(context: Context, configName: str):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
        logger.info(f'User {context.author.name} tried to get a config value: {configName}')
    else:
        configValue = config.get(context.guild.id, configName)
        logger.info(f'User {context.author.name} sucessfully read a config value: {configName} -> {configValue}')
        return configValue

async def sendMessage(context: Context, content: str):
    guild_id = context.guild.id
    channel = context.guild.get_channel(config.get(guild_id, config.BOT_CHANNEL))
    if channel is None:
        channel = context.channel
    await channel.send(content)
    logger.info(f'Bot sent the following message to {context.channel.name}: {content}')

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
