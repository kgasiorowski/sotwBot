import discord
from discord.ext import commands
from discord.ext.commands.context import Context
import secret
from config import config
from utils import logger

bot = commands.Bot(command_prefix='!', description='Skill of the Week Bot', intents=discord.Intents.default())
config = config.Config()
logger = logger.initLogger()

@bot.event
async def on_ready():
    print(f'Logged in')
    logger.info('Bot started')

@bot.command()
async def register(context: Context, osrsUsername: str):
    """Registers you for upcoming SOTWs

    If your username has spaces in it, please surround it with quotes, or this command will not work properly.
    Example: !register "Crotch Flame"
    """
    guildId = context.guild.id
    discordUserId = context.author.id

    config.addParticipant(guildId, osrsUsername, discordUserId)

    await context.message.delete(delay=30)
    messageContent = context.author.mention + f'''
    You have been registered as {osrsUsername}.\n
    If this isn't right, you can run the command again and you will be re-registered under your new name.\n
    This message will be automatically deleted in one minute.
    '''
    await sendMessage(context, messageContent, delete_after=30)

async def canRunAdmin(context: Context):
    """
    Determines if the user invoking the command is allowed to run admin commands.
    """
    isAdminUser = False
    allowedRoleId = config.get(context.guild.id, config.ADMIN_ROLE)
    if allowedRoleId is None:
        for role in context.author.roles:
            if 'admin' in role.name.lower():
                isAdminUser = True
                break
    else:
        allowedRole = context.guild.get_role(allowedRoleId)
        isAdminUser = allowedRole in context.author.roles

    if not isAdminUser:
        if context.invoked_with != 'help':
            await sendMessage(context, config.PERMISSION_ERROR_MESSAGE, isAdmin=False)
            logger.info(f'User {context.author.name} tried to perform an admin action: {context.invoked_subcommand}')
        return False
    return True

@bot.group(checks=[canRunAdmin], case_insensitive=True)
async def admin(context: Context):
    """This denotes a command which requires the special admin role to run.
    """

@admin.command()
async def setAdminRole(context: Context, role: discord.Role):
    """Sets the user role which can interact with the bot
    If no role is set, it will default to any role with "Admin" in the name.
    """
    config.set(context.guild.id, config.ADMIN_ROLE, role.id)
    await sendMessage(context, 'Mod role successfully set', isAdmin=True)
    logger.info(f'User {context.author.name} successfully set the bot role to {role.name}')

@admin.command()
async def setAdminChannel(context: Context, channel: discord.TextChannel):
    """This sets the channel that this bot will use for admin purposes
    If not set, the bot will simply respond in the same channel.
    The bot will still listen to all channels for commands.
    """
    config.set(context.guild.id, config.BOT_ADMIN_CHANNEL, channel.id)
    await sendMessage(context, 'Bot admin channel successfully set', isAdmin=True)
    logger.info(f'User {context.author.name} successfully set the bot channel to {channel.name}')

@admin.command()
async def setPublicChannel(context: Context, channel: discord.TextChannel):
    """This sets the channel that this bot will use for admin purposes
    If not set, the bot will simply respond in the same channel.
    The bot will still listen to all channels for commands.
    """
    config.set(context.guild.id, config.BOT_PUBLIC_CHANNEL, channel.id)
    await sendMessage(context, 'Bot public channel successfully set', isAdmin=True)
    logger.info(f'User {context.author.name} successfully set the bot channel to {channel.name}')

@admin.command()
async def setClanName(context: Context, clanName: str):
    """Set the clan's name
    """
    config.set(context.guild.id, config.CLAN_NAME, clanName)
    logger.info(f'User {context.author.name} set a configuration value: {config.CLAN_NAME} -> {clanName}')
    await sendMessage(context, 'Successfully updated clan name', isAdmin=True)

@admin.command()
async def getClanName(context: Context):
    """Retrieves the clan name for the current discord, if set
    """
    clanName = config.get(context.guild.id, config.CLAN_NAME)
    logger.info(f'User {context.author.name} sucessfully read a config value: {config.CLAN_NAME} -> {clanName}')
    await sendMessage(context, f'Clan Name -> {clanName if clanName is not None else "Not set"}', isAdmin=True)

@admin.command()
async def setSOTWNumber(context: Context, sotwnumber: int):
    """Set the clan's sequential sotw number
    """
    config.set(context.guild.id, config.SOTW_NUMBER, sotwnumber)
    logger.info(f'User {context.author.name} set a configuration value: {config.SOTW_NUMBER} -> {sotwnumber}')
    await sendMessage(context, 'Successfully updated SOTW number', isAdmin=True)

@admin.command()
async def getSOTWNumber(context: Context):
    """Retrieves the sotw number for the current discord, if set
    """
    sotwNumber = config.get(context.guild.id, config.SOTW_NUMBER)
    logger.info(f'User {context.author.name} sucessfully read a config value: {config.SOTW_NUMBER} -> {sotwNumber}')
    await sendMessage(context, f'SOTW Number -> {sotwNumber if sotwNumber is not None else "Not set"}', isAdmin=True)

async def sendMessage(context: Context, content: str, isAdmin: bool=False, delete_after=None):
    guild_id = context.guild.id
    configKey = config.BOT_ADMIN_CHANNEL if isAdmin else config.BOT_PUBLIC_CHANNEL
    channel = context.guild.get_channel(config.get(guild_id, configKey))
    if channel is None:
        channel = context.channel
    logger.info(f'Bot sent the following message to {context.channel.name}: {content}')
    return await channel.send(content, delete_after=delete_after)

if __name__ == "__main__":
    bot.run(secret.TOKEN)
