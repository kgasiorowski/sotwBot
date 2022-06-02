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

async def adminRunCallback(context: Context):
    if not checkRole(context):
        await sendMessage(context, config.PERMISSION_ERROR_MESSAGE)
        logger.info(f'User {context.author.name} tried to perform an admin action: {context.invoked_subcommand}')
        return False
    return True

@bot.group(checks=[adminRunCallback], case_insensitive=True)
async def admin(context: Context):
    pass

@admin.command()
async def setRole(context: Context, role: discord.Role):
    """Sets the user role which can interact with the bot
    If no role is set, it will default to any role with "Admin" in the name.
    """
    config.set(context.guild.id, config.ADMIN_ROLE, role.id)
    await sendMessage(context, 'Mod role successfully set')
    logger.info(f'User {context.author.name} successfully set the bot role to {role.name}')

@admin.command()
async def setChannel(context: Context, channel: discord.TextChannel):
    """This sets the channel that this bot will use
    If not set, the bot will simply respond in the same channel.
    The bot will still listen to all channels for commands.
    """
    config.set(context.guild.id, config.BOT_CHANNEL, channel.id)
    await sendMessage(context, 'Bot channel successfully set')
    logger.info(f'User {context.author.name} successfully set the bot channel to {channel.name}')

@admin.command()
async def setclanname(context: Context, clanName: str):
    """Set the clan's name
    """
    config.set(context.guild.id, config.CLAN_NAME, clanName)
    logger.info(f'User {context.author.name} set a configuration value: {config.CLAN_NAME} -> {clanName}')
    await sendMessage(context, 'Successfully updated clan name')

@admin.command()
async def getclanname(context: Context):
    """Retrieves the clan name for the current discord, if set
    """
    clanName = config.get(context.guild.id, config.CLAN_NAME)
    logger.info(f'User {context.author.name} sucessfully read a config value: {config.CLAN_NAME} -> {clanName}')
    await sendMessage(context, f'Clan Name -> {clanName if clanName is not None else "Not set"}')

@admin.command()
async def setsotwnumber(context: Context, sotwnumber: int):
    """Set the clan's sequential sotw number
    """
    config.set(context.guild.id, config.SOTW_NUMBER, sotwnumber)
    logger.info(f'User {context.author.name} set a configuration value: {config.SOTW_NUMBER} -> {sotwnumber}')
    await sendMessage(context, 'Successfully updated SOTW number')

@admin.command()
async def getsotwnumber(context: Context):
    """Retrieves the sotw number for the current discord, if set
    """
    sotwNumber = config.get(context.guild.id, config.SOTW_NUMBER)
    logger.info(f'User {context.author.name} sucessfully read a config value: {config.SOTW_NUMBER} -> {sotwNumber}')
    await sendMessage(context, f'SOTW Number -> {sotwNumber if sotwNumber is not None else "Not set"}')

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
