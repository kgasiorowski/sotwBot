import discord
from discord.ext import commands
from discord.ext.commands.context import Context
import secret
from config import config
from utils import logger
from datetime import datetime
from datetime import timedelta

bot = commands.Bot(command_prefix='!', description='Skill of the Week Bot', intents=discord.Intents.default())
config = config.Config()
logger = logger.initLogger()

@bot.event
async def on_ready():
    print(f'Logged in')
    logger.info('Bot started')

async def commandIsInBotPublicChannel(context: Context):
    """
    Checks if the command was run in the public bot channel
    """
    publicChannelId = config.get(context.guild.id, config.BOT_PUBLIC_CHANNEL)
    # If there's no admin channel, we don't care. Let the command run.
    if publicChannelId is None:
        return True
    publicChannel = context.guild.get_channel(publicChannelId)
    return context.channel == publicChannel

async def commandIsInAdminChannel(context: Context):
    """
    Checks if the admin command was run in the admin channel.
    """
    adminChannelId = config.get(context.guild.id, config.BOT_ADMIN_CHANNEL)
    # If there's no admin channel, we don't care. Let the command run.
    if adminChannelId is None:
        return True
    adminChannel = context.guild.get_channel(adminChannelId)
    return context.channel == adminChannel

async def userCanRunAdmin(context: Context):
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
            await context.send(config.PERMISSION_ERROR_MESSAGE)
            logger.info(f'User {context.author.name} tried to perform an admin action: {context.invoked_subcommand}')

    return isAdminUser

async def sendMessage(context: Context, content: str, isAdmin: bool=False, delete_after=None):
    guild_id = context.guild.id
    configKey = config.BOT_ADMIN_CHANNEL if isAdmin else config.BOT_PUBLIC_CHANNEL
    channel = context.guild.get_channel(config.get(guild_id, configKey))
    if channel is None:
        channel = context.channel
    logger.info(f'Bot sent the following message to {context.channel.name}: {content}')
    return await channel.send(content, delete_after=delete_after)

# SOTW commands
@bot.command(name="status", checks=[commandIsInBotPublicChannel])
async def checkSOTWStatus(context: Context):
    """Prints the current SOTW status.
    """
    guildId = context.guild.id
    status = config.get(guildId, config.GUILD_STATUS)
    if status is None:
        config.set(guildId, config.GUILD_STATUS, config.SOTW_NONE_PLANNED)
        status = config.SOTW_NONE_PLANNED

    if status == config.SOTW_NONE_PLANNED:
        await sendMessage(context, 'There is no SOTW event planned yet.')
    elif status == config.SOTW_SCHEDULED:
        await sendMessage(context, 'There is a SOTW event scheduled, but it has not yet started.')
    elif status == config.SOTW_IN_PROGRESS:
        await sendMessage(context, 'There is a SOTW event currently in progress.')
    elif status == config.SOTW_CONCLUDED:
        await sendMessage(context, 'The last SOTW event has concluded.')

@bot.command(check=[commandIsInBotPublicChannel])
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

@bot.group(checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def admin(context: Context):
    """This denotes a command which requires the special admin role to run.
    """
    if context.invoked_subcommand is None:
        await sendMessage(context, 'Admin needs a subcommand to do anything - type !help for more information', isAdmin=True)

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
async def setSOTWTitle(context: Context, SOTWtitle: str):
    """Sets the next SOTW's title
    """
    config.set(context.guild.id, config.SOTW_TITLE, SOTWtitle)
    logger.info(f'User {context.author.name} set the SOTW\'s title to: {SOTWtitle}')
    await sendMessage(context, 'Successfully updated SOTW title', isAdmin=True)

@admin.command()
async def getSOTWNumber(context: Context):
    """Retrieves the sotw number for the current discord, if set
    """
    sotwNumber = config.get(context.guild.id, config.SOTW_NUMBER)
    logger.info(f'User {context.author.name} sucessfully read a config value: {config.SOTW_NUMBER} -> {sotwNumber}')
    await sendMessage(context, f'SOTW Number -> {sotwNumber if sotwNumber is not None else "Not set"}', isAdmin=True)

@admin.command(name="create")
async def createSOTW(context: Context, dateString: str, duration: str, metric: str=None):
    """Schedules a SOTW event. Expects a date in descending order (YEAR/MONTH/DAY)
    This will schedule a SOTW which will start at midnight ON THAT DATE.
    So, for example, giving it the date 2022/1/1 will schedule a SOTW to start on 12:00am on January 1st, 2022.
    """
    sotwStartDate = datetime.strptime(dateString, '%Y/%m/%d')
    sotwStartDate = sotwStartDate.replace(hour=0, minute=0, second=0)
    number = int(duration[0])
    timeUnit = duration[1]

    if timeUnit == 'd':
        duration = timedelta(days=number)
    elif timeUnit == 'w':
        duration = timedelta(weeks=number)

    sotwEndDate = sotwStartDate + duration

    if metric is None:
        ... # Check if the metric has been set by the poll yet

@admin.command(name="openpoll")
async def openSOTWPoll(context: Context, skillsString: str):
    """Open a SOTW poll in the public channel for users to vote on the next skill.
    Expects a comma-delimited string of possible skills to choose from.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status == config.SOTW_POLL_OPENED:
        await sendMessage(context, 'There is already a poll currently running.', isAdmin=True)
        return

    pollContent = config.POLL_CONTENT
    skills = skillsString.split(',')
    for i in range(len(skills)):
        pollContent += '\n' + config.POLL_REACTIONS[i] + ' - ' + skills[i].capitalize() + '\n'

    poll = await sendMessage(context, pollContent)

    for i in range(len(skills)):
        await poll.add_reaction(config.POLL_REACTIONS[i])

    config.set(context.guild.id, config.SKILLS_BEING_POLLED, skills)
    config.set(context.guild.id, config.CURRENT_POLL, poll.id)
    config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_POLL_OPENED)

@admin.command(name="closepoll")
async def closeSOTWPoll(context: Context):
    """Closes the current SOTW poll, if it exists.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status != config.SOTW_POLL_OPENED:
        await sendMessage(context, 'There\'s no poll currently running.', isAdmin=True)
    else:
        poll = await config.getGuildPublicChannel(context.guild).fetch_message(config.get(context.guild.id, config.CURRENT_POLL))
        skillsBeingPolled = config.get(context.guild.id, config.SKILLS_BEING_POLLED)
        config.set(context.guild.id, config.CURRENT_POLL, None)
        config.set(context.guild.id, config.SKILLS_BEING_POLLED, [])

        winner = None
        mostReactions = 0
        for i in range(len(poll.reactions)):
            if poll.reactions[i].count > mostReactions:
                winner = skillsBeingPolled[i]
                mostReactions = poll.reactions[i].count

        config.set(context.guild.id, config.POLL_WINNER, winner)
        await poll.edit(content='This poll has closed.')
        await sendMessage(context, f'Current poll closed. Winner: {winner}', isAdmin=True)
        await sendMessage(context, f'The SOTW poll has closed! The winner is: {winner}', isAdmin=False)

if __name__ == "__main__":
    bot.run(secret.TOKEN)
