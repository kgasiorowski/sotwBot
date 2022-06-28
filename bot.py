import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from discord import Guild
from discord import TextChannel
import secret
from config import config
from utils import logger
from datetime import datetime
from datetime import timedelta
import WiseOldManApi

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', description='Skill of the Week Bot', intents=intents)
config = config.Config()
logger = logger.initLogger()

@bot.event
async def on_ready():
    print(f'Logged in')
    logger.info('Bot started')

def commandIsInBotPublicChannel(context: Context):
    """
    Checks if the command was run in the public bot channel
    """
    publicChannelId = config.get(context.guild.id, config.BOT_PUBLIC_CHANNEL)
    # If there's no admin channel, we don't care. Let the command run.
    if publicChannelId is None:
        return True
    publicChannel = context.guild.get_channel(publicChannelId)
    return context.channel == publicChannel

def commandIsInAdminChannel(context: Context):
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

async def sendMessage(guild: Guild, defaultChannel: TextChannel, content: str, isAdmin: bool=False, delete_after=None):
    guild_id = guild.id
    configKey = config.BOT_ADMIN_CHANNEL if isAdmin else config.BOT_PUBLIC_CHANNEL
    channel = guild.get_channel(config.get(guild_id, configKey))
    if channel is None:
        channel = defaultChannel
    logger.info(f'Bot sent the following message to {channel.name}: {content}')
    return await channel.send(content, delete_after=delete_after)

def getSotwRanks(sotwData: dict):
    sortedParticipants = sorted(sotwData['participants'], key=lambda a: a['progress']['gained'], reverse=True)
    return [(a['username'], a['progress']['gained']) for a in sortedParticipants]

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
        await sendMessage(context.guild, context.channel, 'There is no SOTW event planned yet.')
    elif status == config.SOTW_SCHEDULED:
        sotwId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
        sotwData = WiseOldManApi.getSotw(sotwId)
        content = getSOTWStatusContent(context, sotwData)
        await sendMessage(context.guild, context.channel, 'There is a SOTW planned, but not yet started.' + content)
    elif status == config.SOTW_IN_PROGRESS:
        sotwId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
        sotwData = WiseOldManApi.getSotw(sotwId)
        hiscores = getSotwRanks(sotwData)[:3]
        content = 'There is a SOTW event currently in progress.' + getSOTWStatusContent(context, sotwData)
        content += '\n Current leaders:\n-----------------------'
        for username, exp in hiscores:
            content += f'\n {username} - {exp:,} xp'

        content += f'\n\nFor the full competition data, click this link: https://wiseoldman.net/competitions/{sotwId}/'
        await sendMessage(context.guild, context.channel, content)

    elif status == config.SOTW_CONCLUDED:
        await sendMessage(context.guild, context.channel, 'The last SOTW event has concluded.')

def getSOTWStatusContent(context: Context, sotwData):
    rawDateFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
    desiredDateFormat = '%B %d, %I%p GMT (%A)'

    rawStartDateString = sotwData['startsAt']
    rawEndDateString = sotwData['endsAt']

    startDate = datetime.strptime(rawStartDateString, rawDateFormat).strftime(desiredDateFormat)
    endDate = datetime.strptime(rawEndDateString, rawDateFormat).strftime(desiredDateFormat)

    return f"""
    Skill: {config.get(context.guild.id, config.POLL_WINNER)}
    Start date: {startDate}
    End date: {endDate}
    """

@bot.command(check=[commandIsInBotPublicChannel])
async def register(context: Context, osrsUsername: str):
    """Registers you for upcoming SOTWs

    If your username has spaces in it, please surround it with quotes, or this command will not work properly.
    Example: !register "Crotch Flame"
    """
    guildId = context.guild.id
    discordUserId = context.author.id

    config.addParticipant(guildId, osrsUsername, discordUserId)

    messageContent = context.author.mention + f'''
    You have been registered as {osrsUsername}.\n
    If this isn't right, you can run the command again and you will be re-registered under your new name.\n
    This message will be automatically deleted in thirty seconds.
    '''
    await sendMessage(context.guild, context.channel, messageContent, delete_after=30)
    await context.message.delete(delay=30)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def setAdminRole(context: Context, role: discord.Role):
    """Sets the user role which can interact with the bot
    If no role is set, it will default to any role with "Admin" in the name.
    """
    config.set(context.guild.id, config.ADMIN_ROLE, role.id)
    await sendMessage(context.guild, context.channel, 'Mod role successfully set', isAdmin=True)
    logger.info(f'User {context.author.name} successfully set the bot role to {role.name}')

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def setAdminChannel(context: Context, channel: discord.TextChannel):
    """This sets the channel that this bot will use for admin purposes
    If not set, the bot will simply respond in the same channel.
    The bot will still listen to all channels for commands.
    """
    config.set(context.guild.id, config.BOT_ADMIN_CHANNEL, channel.id)
    await sendMessage(context.guild, context.channel, 'Bot admin channel successfully set', isAdmin=True)
    logger.info(f'User {context.author.name} successfully set the bot channel to {channel.name}')

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def setPublicChannel(context: Context, channel: discord.TextChannel):
    """This sets the channel that this bot will use for admin purposes
    If not set, the bot will simply respond in the same channel.
    The bot will still listen to all channels for commands.
    """
    config.set(context.guild.id, config.BOT_PUBLIC_CHANNEL, channel.id)
    await sendMessage(context.guild, context.channel, 'Bot public channel successfully set', isAdmin=True)
    logger.info(f'User {context.author.name} successfully set the bot channel to {channel.name}')

@bot.command(name="settitle", checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def setSOTWTitle(context: Context, SOTWtitle: str=None):
    """Sets the next SOTW's title
    """
    config.set(context.guild.id, config.SOTW_TITLE, SOTWtitle)
    if SOTWtitle is None:
        await sendMessage(context.guild, context.channel, 'Successfully reset SOTW title', isAdmin=True)
    else:
        await sendMessage(context.guild, context.channel, 'Successfully updated SOTW title', isAdmin=True)

@bot.command(name="create", checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def createSOTW(context: Context, dateString: str, duration: str, metric: str=None):
    """Schedules a SOTW event. Expects a date in descending order (YEAR/MONTH/DAY)
    This will schedule a SOTW which will start at midnight ON THAT DATE.
    So, for example, giving it the date 2022/1/1 will schedule a SOTW to start on 12:00am on January 1st, 2022.
    """

    if metric is None:
        metric = config.get(context.guild.id, config.POLL_WINNER)

    if metric is None:
        errorMessageContent = """
        Couldn\'t start a sotw - there was no metric registered. A metric is automatically saved when a poll is closed,
        or you can manually pass in a skill with this command, after the duration.
        """
        await sendMessage(context.guild, context.channel, errorMessageContent, isAdmin=True)
        return

    sotwStartDate = datetime.strptime(dateString, '%Y/%m/%d')
    sotwStartDate = sotwStartDate.replace(hour=0, minute=0, second=0)
    number = int(duration[0])
    timeUnit = duration[1]

    if timeUnit == 'd':
        duration = timedelta(days=number)
    elif timeUnit == 'w':
        duration = timedelta(weeks=number)

    sotwEndDate = sotwStartDate + duration
    title = config.get(context.guild.id, config.SOTW_TITLE)
    if title is None:
        await sendMessage(context.guild, context.channel, 'Couldn\'t create SOTW - no title was set.', isAdmin=True)
        return

    groupId = config.get(context.guild.id, config.WOM_GROUP_ID)
    groupVerificationCode = config.get(context.guild.id, config.WOM_GROUP_VERIFICATION_CODE)

    if groupId is None or groupVerificationCode is None:
        participants = config.getParticipantList(context.guild.id)
        if participants is None:
            await sendMessage(context.guild, context.channel, 'Couldn\'t create SOTW - either no WOM group has been specified, or nobody has registered, as there is no participant list.', isAdmin=True)
            return
        elif len(participants) == 1:
            await sendMessage(context.guild, context.channel, 'Couldn\'t create SOTW - needs more than one competitors.', isAdmin=True)
            return
        response = WiseOldManApi.createSOTW(title, metric, sotwStartDate, sotwEndDate, participants=participants)
    else:
        response = WiseOldManApi.createSOTW(title, metric, sotwStartDate, sotwEndDate, groupId=groupId, groupVerificationCode=groupVerificationCode)

    if not response:
        await sendMessage(context.guild, context.channel, 'There was an error with the api. Please check the logs.', isAdmin=True)
    else:
        await sendMessage(context.guild, context.channel, 'SOTW successfully scheduled. Type !status in the public channel to see the current SOTW status.', isAdmin=True)
        config.set(context.guild.id, config.SOTW_COMPETITION_ID, response['id'])
        config.set(context.guild.id, config.SOTW_START_DATE, response['startsAt'])
        config.set(context.guild.id, config.SOTW_END_DATE, response['endsAt'])
        if 'verificationCode' in response:
            verificationCode = response['verificationCode']
        else:
            verificationCode = None
        config.set(context.guild.id, config.SOTW_VERIFICATION_CODE, verificationCode)
        config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_SCHEDULED)

@bot.command(name="openpoll", checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def openSOTWPoll(context: Context, skillsString: str):
    """Open a SOTW poll in the public channel for users to vote on the next skill.
    Expects a comma-delimited string of possible skills to choose from.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status == config.SOTW_POLL_OPENED:
        await sendMessage(context.guild, context.channel, 'There is already a poll currently running.', isAdmin=True)
        return

    pollContent = config.POLL_CONTENT
    skills = skillsString.split(',')
    for i in range(len(skills)):
        pollContent += f'\n{config.POLL_REACTIONS_NUMERICAL[i]} - {skills[i].capitalize()}\n'

    poll = await sendMessage(context.guild, context.channel, pollContent)

    for i in range(len(skills)):
        await poll.add_reaction(config.POLL_REACTIONS_NUMERICAL[i])

    config.set(context.guild.id, config.SKILLS_BEING_POLLED, skills)
    config.set(context.guild.id, config.CURRENT_POLL, poll.id)
    config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_POLL_OPENED)

@bot.command(name="closepoll", checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def closeSOTWPoll(context: Context):
    """Closes the current SOTW poll, if it exists.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status != config.SOTW_POLL_OPENED:
        await sendMessage(context.guild, context.channel, 'There\'s no poll currently running.', isAdmin=True)
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
        config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_POLL_CLOSED)
        await sendMessage(context.guild, context.channel, f'Current poll closed. Winner: {winner}', isAdmin=True)
        await sendMessage(context.guild, context.channel, f'The SOTW poll has closed! The winner is: {winner}', isAdmin=False)

@bot.command(name='setgroup', checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def setSotwGroup(context: Context, groupId: int=None, groupVerificationCode: str=None):
    """Sets the custom WOM group for this discord. Optional, and if no parameters are provided, will reset the group.
    """
    config.set(context.guild.id, config.WOM_GROUP_ID, groupId)
    config.set(context.guild.id, config.WOM_GROUP_VERIFICATION_CODE, groupVerificationCode)
    if groupId is None or groupVerificationCode is None:
        messageContent = 'The group has been reset.'
    else:
        messageContent = 'The group ID and verification code have been saved.'
    await sendMessage(context.guild, context.channel, messageContent, isAdmin=True)

@bot.command(name='deletesotw', checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def deleteSotw(context: Context):
    """Deletes the current SOTW
    """
    sotwId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
    verificationCode = \
        config.get(context.guild.id, config.WOM_GROUP_VERIFICATION_CODE) or \
        config.get(context.guild.id, config.SOTW_VERIFICATION_CODE)

    response = WiseOldManApi.deleteSotw(sotwId, verificationCode)

    if response:
        config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_NONE_PLANNED)
        config.set(context.guild.id, config.SOTW_COMPETITION_ID, None)
        config.set(context.guild.id, config.SOTW_VERIFICATION_CODE, None)
        config.set(context.guild.id, config.SOTW_START_DATE, None)
        config.set(context.guild.id, config.SOTW_END_DATE, None)
        await sendMessage(context, 'SOTW deletion successful', isAdmin=True)
    else:
        await sendMessage(context, 'SOTW deletion failed - see logs', isAdmin=True)

@bot.command(name='finishsotw', checks=[userCanRunAdmin, commandIsInAdminChannel], case_insensitive=True)
async def finishSotw(context: Context):
    """Ends the currently running SOTW, if there is one.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status not in [config.SOTW_IN_PROGRESS, config.SOTW_SCHEDULED]:
        await sendMessage(context, 'Couldn\'t end the sotw - one is not currently running.', isAdmin=True)
        return

    sotwCompetitionId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
    sotwData = WiseOldManApi.getSotw(sotwCompetitionId)
    hiscores = getSotwRanks(sotwData)
    content = f'{config.get(context.guild.id, config.SOTW_TITLE)} has ended!\nThe winners are:'
    i = 1
    for username, exp in hiscores[:3]:
        discordUserId = config.getParticipant(context.guild.id, username)
        content += f'\n{i}. {username} '
        if discordUserId is not None:
            user = context.guild.get_member(discordUserId)
            content += f'({user.mention}) '
        content += f'- {exp:,} xp'
        i += 1
    content += '\nPlease contact any officer for your rewards.'
    await sendMessage(context, content, isAdmin=False)

    config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_CONCLUDED)

    config.set(context.guild.id, config.SOTW_COMPETITION_ID, None)
    config.set(context.guild.id, config.SOTW_VERIFICATION_CODE, None)
    config.set(context.guild.id, config.SOTW_START_DATE, None)
    config.set(context.guild.id, config.SOTW_END_DATE, None)

if __name__ == "__main__":
    bot.run(secret.TOKEN)
