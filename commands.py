import discord
import discord.utils
from discord.ext.commands.context import Context
import secret
from config import config
from utils import logger
from datetime import datetime
from datetime import timedelta
from api import WiseOldManApi
from SOTWBot import SOTWBot

intents = discord.Intents.default()
intents.members = True
bot = SOTWBot(command_prefix='', description='Skill of the Week Bot', intents=intents)
config = config.Config()
logger = logger.getLogger()

@bot.event
async def on_ready():
    print(f'Logged in')
    logger.info('Bot started')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Prefix stuff
    if message.guild is not None:
        prefix = config.get(message.guild.id, config.COMMAND_PREFIX)
        prefix = prefix if prefix is not None else ''
        if not message.content.startswith(prefix):
            return
        message.content = message.content.removeprefix(prefix)
        await bot.process_commands(message)
        return

    # Handle commands given in direct messages to the bot
    else:
        return
        guildId = config.getGuildByDmId(message.channel.id)
        if guildId is not None:
            context = await bot.get_context(message)
            guild = bot.get_guild(int(guildId))
            context.guild = guild
            if message.content.lower().startswith('done'):
                if config.get(context.guild.id, config.GUILD_STATUS) != config.SOTW_CONCLUDED:
                    return
                poll = await context.channel.fetch_message(config.get(context.guild.id, config.CURRENT_POLL))

                skillsVotedForCounter = len(list(filter(lambda reaction: reaction.count >= 1, poll.reactions)))
                if skillsVotedForCounter < 3:
                    await message.channel.send('It seems like you haven\'t picked three skills yet. Please add your reactions and try again.')
                    return

                skills = config.SOTW_SKILLS.copy()
                skills.remove(config.get(context.guild.id, config.SOTW_PREVIOUS_SKILL))
                winners = sorted(
                    [(skills[i], poll.reactions[i]) for i in range(len(skills))],
                    key=lambda a: a[1].count,
                    reverse=True)[:3]
                winners = [winner[0] for winner in winners]
                await createPoll(context, winners)
                await message.channel.send('Thanks for your selection!')

def commandIsInBotPublicChannel(context: Context):
    """
    Checks if the command was run in the public bot channel
    """
    publicChannelId = config.get(context.guild.id, config.BOT_PUBLIC_CHANNEL)
    # If there's no public channel, we don't care. Let the command run.
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
    allowedRoleId = config.get(context.guild.id, config.ADMIN_ROLE)
    if allowedRoleId is None:
        isAdminUser = discord.utils.find(lambda role:'admin' in role.name.lower(), context.author.roles) is not None
    else:
        isAdminUser = context.guild.get_role(allowedRoleId) in context.author.roles

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
    logger.info(f'Bot sent a message to channel {channel.name}: {content}')
    return await channel.send(content, delete_after=delete_after)

def getSotwRanks(sotwData: dict):
    sortedParticipants = sorted(sotwData['participants'], key=lambda a: a['progress']['gained'], reverse=True)
    return [(a['displayName'], a['progress']['gained']) for a in sortedParticipants]

@bot.command(name="setprefix", checks=[userCanRunAdmin, commandIsInAdminChannel])
async def setprefix(context: Context, prefix: str):
    """Sets the prefix this bot will use.
    If not set, the bot will attempt to parse every message regardless of the prefix given.
    """
    logger.info(f'User {context.author.name} changed the prefix to {prefix}')
    config.set(context.guild.id, config.COMMAND_PREFIX, prefix)
    await sendMessage(context, f'Prefix successfully updated to {prefix}', isAdmin=True)

# SOTW commands
@bot.command(name="status", checks=[commandIsInBotPublicChannel])
async def checkSOTWStatus(context: Context):
    """Prints the current SOTW status.
    """
    guildId = context.guild.id
    status = config.get(guildId, config.GUILD_STATUS)
    logger.info(f'User {context.author.name} asked for the status ({status})')
    if status is None:
        config.set(guildId, config.GUILD_STATUS, config.SOTW_NONE_PLANNED)
        status = config.SOTW_NONE_PLANNED

    if status in [config.SOTW_NONE_PLANNED, config.SOTW_POLL_OPENED, config.SOTW_POLL_CLOSED]:
        await sendMessage(context, 'There is no SOTW event planned yet. It might be being polled.')
    elif status == config.SOTW_SCHEDULED:
        sotwId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
        sotwData = WiseOldManApi.getSotw(sotwId)
        content = getSOTWStatusContent(sotwData)
        await sendMessage(context, 'There is a SOTW planned, but not yet started.' + content)
    elif status == config.SOTW_IN_PROGRESS:
        sotwId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
        sotwData = WiseOldManApi.getSotw(sotwId)
        hiscores = getSotwRanks(sotwData)[:10]
        content = 'There is a SOTW event currently in progress.' + getSOTWStatusContent(sotwData)
        content += '\n Current leaders:\n-----------------------'
        counter = 1
        for username, exp in hiscores:
            if exp <= 0:
                break
            content += f'\n{counter}. {username} - {exp:,} xp'
            counter += 1
        await sendMessage(context, content)
    elif status == config.SOTW_CONCLUDED:
        await sendMessage(context, 'The previous SOTW event has concluded.')

def getSOTWStatusContent(sotwData: dict):
    rawDateFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
    desiredDateFormat = '%B %d, %I%p GMT (%A)'

    rawStartDateString = sotwData['startsAt']
    rawEndDateString = sotwData['endsAt']

    startDate = datetime.strptime(rawStartDateString, rawDateFormat).strftime(desiredDateFormat)
    endDate = datetime.strptime(rawEndDateString, rawDateFormat).strftime(desiredDateFormat)

    return f"""
    Skill: {sotwData['metric'].capitalize()}
    Start date: {startDate}
    End date: {endDate}
    URL: https://wiseoldman.net/competitions/{sotwData['id']}
    """

@bot.command(check=[commandIsInBotPublicChannel])
async def register(context: Context, *args):
    """Registers you for upcoming SOTWs
    """
    osrsUsername = ' '.join(args)

    if not osrsUsername or osrsUsername.isspace():
        messageContent = context.author.mention + ', you didn\'t give any username. Please try again with a username.'
        await sendMessage(context, messageContent, isAdmin=False, delete_after=30)
        return

    # For whatever reason, underscores get converted to spaces in WOM
    osrsUsername = osrsUsername.replace('_', ' ')

    guildId = context.guild.id
    discordUserId = context.author.id
    config.addParticipant(guildId, osrsUsername, discordUserId)
    messageContent = context.author.mention + f'''
    You have been registered as {osrsUsername}.\n
    If this isn't right, you can run the command again and you will be re-registered under your new name.\n
    This message will be automatically deleted in thirty seconds.
    '''
    logger.info(f'User {context.author.name} registered themselves as {osrsUsername}')
    await sendMessage(context, messageContent, delete_after=30)
    await context.message.delete(delay=30)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def reloadconfigs(context: Context):
    """Reloads the configuration json after a manual change
    Only used for development and when shit breaks
    """
    logger.info(f'User {context.author.name} reloaded the configurations')
    config.load()
    await sendMessage(context, 'Configuration reload successful', isAdmin=True)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def setadminrole(context: Context, role: discord.Role):
    """Sets the user role which can interact with the bot
    If no role is set, it will default to any role with "Admin" in the name.
    """
    config.set(context.guild.id, config.ADMIN_ROLE, role.id)
    await sendMessage(context, 'Mod role successfully set', isAdmin=True)
    logger.info(f'User {context.author.name} set the bot role to {role.name}')

async def setChannel(context: Context, channelType: str, channel: discord.TextChannel):
    if channelType == 'admin':
        guideMessageIds = config.ADMIN_GUIDE_MESSAGE_IDS
        channelTypeConfig = config.BOT_ADMIN_CHANNEL
        existingChannel = config.getGuildAdminChannel(context.guild)
        helpContent = config.ADMIN_GUIDE_MESSAGE_CONTENT
    else:
        guideMessageIds = config.PUBLIC_GUIDE_MESSAGE_IDS
        channelTypeConfig = config.BOT_PUBLIC_CHANNEL
        existingChannel = config.getGuildPublicChannel(context.guild)
        helpContent = config.PUBLIC_GUIDE_MESSAGE_CONTENT

    if existingChannel is not None:
        helpMessageIds = config.get(context.guild.id, guideMessageIds)
        for messageId in helpMessageIds:
            existingHelpMessage = await existingChannel.fetch_message(messageId)
            if existingHelpMessage is not None:
                await existingHelpMessage.delete()
    config.set(context.guild.id, channelTypeConfig, channel.id)
    helpMessage = await sendMessage(context, helpContent, isAdmin=channelType == 'admin')

    await helpMessage.pin()

    config.set(
        context.guild.id,
        guideMessageIds,
        [helpMessage.id, helpMessage.channel.last_message_id]
    )

    await sendMessage(context, f'{channelType.capitalize()} channel successfully updated', isAdmin=True, delete_after=10)
    await context.message.delete(delay=30)
    logger.info(f'User {context.author.name} successfully set the {channelType} channel to {channel.name}')

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def setadminchannel(context: Context, channel: discord.TextChannel):
    """This sets the channel that this bot will use for admin purposes
    If not set, the bot will simply respond in the same channel.
    """
    await setChannel(context, 'admin', channel)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def setpublicchannel(context: Context, channel: discord.TextChannel):
    """This sets the channel that this bot will use for admin purposes
    If not set, the bot will simply respond in the same channel.
    """
    await setChannel(context, 'public', channel)

@bot.command(checks=[commandIsInBotPublicChannel])
async def refresh(context: Context):
    """This refreshes each player in the competition.
    Will do nothing if the competition is already up-to-date.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status != config.SOTW_IN_PROGRESS:
        logger.info(f'User {context.author.name} tried to refresh the sotw but there was not one running')
        return

    sotwId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
    verificationCode = config.get(context.guild.id, config.SOTW_VERIFICATION_CODE)
    WiseOldManApi.updateAllParticipants(sotwId, verificationCode)
    logger.info(f'User {context.author.name} refreshed the current sotw')
    await sendMessage(context, 'The competition has been refreshed.', isAdmin=False)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def settitle(context: Context, *args):
    """Sets the next SOTW's title
    """
    SOTWtitle = ' '.join(args)
    config.set(context.guild.id, config.SOTW_TITLE, SOTWtitle)
    if SOTWtitle is None:
        await sendMessage(context, 'Successfully reset SOTW title', isAdmin=True)
        logger.info('User {context.author.name} reset the SOTW title')
    else:
        await sendMessage(context, f'Successfully updated SOTW title to {SOTWtitle}', isAdmin=True)
        logger.info(f'User {context.author.name} changed the sotw title to {SOTWtitle}')

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def createsotw(context: Context, dateString: str, duration: str, metric: str=None):
    """Schedules a SOTW event. Expects a date in descending order (YEAR/MONTH/DAY)
    This will schedule a SOTW which will start at midnight ON THAT DATE.
    So, for example, giving it the date 2022/1/1 will schedule a SOTW to start on 12:00am on January 1st, 2022.
    """

    logger.info(f'User {context.author.name} is trying to create a SOTW with the following params: '
                f'date: {dateString} '
                f'duration: {duration} '
                f'metric: {metric}')

    if metric is None:
        metric = config.get(context.guild.id, config.POLL_WINNER)

    if metric is None:
        errorMessageContent = """
        Couldn\'t start a sotw - there was no metric registered. A metric is automatically saved when a poll is closed,
        or you can manually pass in a skill with this command, after the duration.
        """
        logger.warning('Could not create sotw, as there was no metric available')
        await sendMessage(context, errorMessageContent, isAdmin=True)
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
        await sendMessage(context, 'Couldn\'t create SOTW - no title was set.', isAdmin=True)
        logger.warning('Could not create sotw, title was missing')
        return

    groupId = config.get(context.guild.id, config.WOM_GROUP_ID)
    groupVerificationCode = config.get(context.guild.id, config.WOM_GROUP_VERIFICATION_CODE)

    if groupId is None or groupVerificationCode is None:
        participants = config.getParticipantList(context.guild.id)
        if participants is None:
            logger.warning('Could not create sotw, no participants')
            await sendMessage(context, 'Couldn\'t create SOTW - either no WOM group has been specified, or nobody has registered, as there is no participant list.', isAdmin=True)
            return
        elif len(participants) == 1:
            logger.warning('Could not create sotw, not enough participants')
            await sendMessage(context, 'Couldn\'t create SOTW - needs more than one competitors.', isAdmin=True)
            return
        response = WiseOldManApi.createSOTW(title, metric, sotwStartDate, sotwEndDate, participants=participants)
    else:
        response = WiseOldManApi.createSOTW(title, metric, sotwStartDate, sotwEndDate, groupId=groupId, groupVerificationCode=groupVerificationCode)

    if not response:
        logger.warning(f'Couldnt start sotw, there was a problem with the api: {response}')
        await sendMessage(context, 'There was an error with the api. Please check the logs.', isAdmin=True)
    else:
        await sendMessage(context, 'SOTW successfully scheduled. Type !status in the public channel to see the current SOTW status.', isAdmin=True)
        await sendMessage(context, 'The next skill of the week has been scheduled!' + getSOTWStatusContent(response), isAdmin=False)

        config.set(context.guild.id, config.SOTW_COMPETITION_ID, response['id'])
        config.set(context.guild.id, config.SOTW_START_DATE, response['startsAt'])
        config.set(context.guild.id, config.SOTW_END_DATE, response['endsAt'])
        if 'verificationCode' in response:
            verificationCode = response['verificationCode']
        else:
            verificationCode = None
        config.set(context.guild.id, config.SOTW_VERIFICATION_CODE, verificationCode)
        config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_SCHEDULED)
        config.set(context.guild.id, config.SOTW_PREVIOUS_SKILL, metric)

async def createPoll(context: Context, skills: list):
    pollContent = config.POLL_CONTENT
    for i in range(len(skills)):
        pollContent += f'\n{config.POLL_REACTIONS_NUMERICAL[i]} - {skills[i].capitalize()}\n'

    poll = await sendMessage(context, pollContent)

    for i in range(len(skills)):
        await poll.add_reaction(config.POLL_REACTIONS_NUMERICAL[i])

    config.set(context.guild.id, config.SKILLS_BEING_POLLED, skills)
    config.set(context.guild.id, config.CURRENT_POLL, poll.id)
    config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_POLL_OPENED)

@bot.command(name="createpoll", checks=[userCanRunAdmin, commandIsInAdminChannel])
async def openpoll(context: Context, *args):
    """Open a SOTW poll in the public channel for users to vote on the next skill.
    Expects space separated skills after the commad.
    """
    if config.get(context.guild.id, config.GUILD_STATUS) == config.SOTW_POLL_OPENED and \
            config.get(context.guild.id, config.SOTW_WINNER_DM_ID) is None:
        logger.info(f'User {context.author.name} couldnt create a poll - one already running')
        await sendMessage(context, 'There is already a poll currently running.', isAdmin=True)
        return

    config.set(context.guild.id, config.SOTW_WINNER_DM_ID, None)
    await createPoll(context, list(args))
    logger.info(f"User {context.author.name} created a poll with skills {' '.join(list(args))}")

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def closepoll(context: Context):
    """Closes the current SOTW poll, if it exists.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status != config.SOTW_POLL_OPENED:
        logger.info(f'User {context.author.name} couldn\'t close poll, one is not opened')
        await sendMessage(context, 'There\'s no poll currently running.', isAdmin=True)
    else:
        poll = await config.getGuildPublicChannel(context.guild).fetch_message(config.get(context.guild.id, config.CURRENT_POLL))
        skillsBeingPolled = config.get(context.guild.id, config.SKILLS_BEING_POLLED)
        # Merge the reactions and skills being polled, then sort them by reaction count and extract the winner
        winner = sorted(
            [{'skill':skillsBeingPolled[i], 'reaction':poll.reactions[i]} for i in range(len(skillsBeingPolled))],
            key=lambda a:a['reaction'].count,
            reverse=True
        )[0]['skill']
        config.set(context.guild.id, config.CURRENT_POLL, None)
        config.set(context.guild.id, config.SKILLS_BEING_POLLED, [])
        config.set(context.guild.id, config.POLL_WINNER, winner)
        config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_POLL_CLOSED)
        logger.info(f'User {context.author.name} closed poll with winner {winner}')
        await sendMessage(context, f'Current poll closed. Winner: {winner}', isAdmin=True)
        await sendMessage(context, f'The SOTW poll has closed! The winner is: {winner}', isAdmin=False)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def cancelPoll(context: Context):
    """Closes the current SOTW poll, if it exists.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status != config.SOTW_POLL_OPENED:
        await sendMessage(context, 'There\'s no poll currently running.', isAdmin=True)
    else:
        try:
            poll = await config.getGuildPublicChannel(context.guild).fetch_message(
                config.get(context.guild.id, config.CURRENT_POLL))
            await poll.delete()
        except:
            logger.warning('Bot tried to delete a poll which was already deleted.')
        config.set(context.guild.id, config.CURRENT_POLL, None)
        config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_NONE_PLANNED)
        await sendMessage(context, 'The poll has been canceled.', isAdmin=False)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def setgroup(context: Context, groupId: int=None, groupVerificationCode: str=None):
    """Sets the custom WOM group for this discord. Optional, and if no parameters are provided, will reset the group.
    """
    config.set(context.guild.id, config.WOM_GROUP_ID, groupId)
    config.set(context.guild.id, config.WOM_GROUP_VERIFICATION_CODE, groupVerificationCode)
    if groupId is None or groupVerificationCode is None:
        messageContent = 'The group has been reset.'
    else:
        messageContent = 'The group ID and verification code have been saved.'
    await sendMessage(context, messageContent, isAdmin=True)
    logger.info(f'User {context.author.id} set the wom group data: '
                f'groupId: {groupId} '
                f'verification: {groupVerificationCode}')

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def deletesotw(context: Context):
    """Deletes the current SOTW. DO NOT USE THIS. USE closepoll INSTEAD.
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
        logger.info(f'User {context.author.name} deleted the current SOTW')
    else:
        logger.info(f'User {context.author.name} tried to delete the current SOTW, but it failed: {response}')
        await sendMessage(context, 'SOTW deletion failed - see logs', isAdmin=True)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def closesotw(context: Context):
    """Ends the currently running SOTW, if there is one.
    """
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status not in [config.SOTW_IN_PROGRESS, config.SOTW_SCHEDULED]:
        await sendMessage(context, 'Couldn\'t end the sotw - one is not currently running.', isAdmin=True)
        logger.info(f'User {context.author.name} tried to end the sotw but there is not one running')
        return

    sotwCompetitionId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
    sotwData = WiseOldManApi.getSotw(sotwCompetitionId)
    metric = sotwData['metric']
    config.set(context.guild.id, config.SOTW_PREVIOUS_SKILL, metric)
    hiscores = getSotwRanks(sotwData)
    sotwTitle = config.get(context.guild.id, config.SOTW_TITLE)
    content = f'{sotwTitle} has ended!\nThe winners are:'
    i = 1
    for username, exp in hiscores[:3]:
        capitalizedUsername, discordUserId = config.getParticipant(context.guild.id, username.lower()) or (username, None)
        content += f'\n{i}. {capitalizedUsername} '
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

    content = "SOTW successfully closed and winner decided. Attempting to send him a DM to choose the possible skills " \
              f"for the next SOTW. If you want to override this, run the {config.get(context.guild.id, config.COMMAND_PREFIX)}openpoll " \
              "command with a list of skills to open a poll manually."
    await sendMessage(context, content, isAdmin=True)

    winner = hiscores[0][0]
    _, winnerId = config.getParticipant(context.guild.id, winner)
    if winnerId is not None:
        winner = context.guild.get_member(winnerId)
        winnerDmChannel = winner.dm_channel if winner.dm_channel is not None else await winner.create_dm()
        content = f"""
        Congratulations on winning {sotwTitle}!\n
        Please choose three skill from the following list, and when you\'re done, reply in this channel with "done"
        """
        for i in range(len(config.SOTW_SKILLS)):
            if config.SOTW_SKILLS[i] == metric:
                continue
            content += f'\n{config.POLL_REACTIONS_ALPHABETICAL[i]} - {config.SOTW_SKILLS[i].capitalize()}'

        message = await winnerDmChannel.send(content)

        for i in range(len(config.SOTW_SKILLS)):
            await message.add_reaction(config.POLL_REACTIONS_ALPHABETICAL[i])

        config.set(context.guild.id, config.CURRENT_POLL, message.id)
        config.set(context.guild.id, config.SOTW_WINNER_DM_ID, winnerDmChannel.id)
    else:
        content = f"""
        The SOTW winner was not registered in discord, so I don't know who to DM for poll options. 
        In order to create a poll for the next SOTW, please choose three skills (or ask the winner to choose) and type 
        `{config.get(context.guild.id, config.COMMAND_PREFIX)}createpoll comma,separated,skills`
        """
        await sendMessage(context, content, isAdmin=True)
        config.set(context.guild.id, config.CURRENT_POLL, None)

@bot.command(checks=[userCanRunAdmin, commandIsInAdminChannel])
async def startsotw(context: Context):
    status = config.get(context.guild.id, config.GUILD_STATUS)
    if status != config.SOTW_SCHEDULED:
        await sendMessage(context, 'Couldn\'t start the sotw, as there is none planned', isAdmin=True)
        return

    config.set(context.guild.id, config.GUILD_STATUS, config.SOTW_IN_PROGRESS)
    sotwId = config.get(context.guild.id, config.SOTW_COMPETITION_ID)
    content = 'The SOTW has begun!'
    content += f'\n\nFor the full competition data, click this link: https://wiseoldman.net/competitions/{sotwId}/'
    await sendMessage(context, content)

if __name__ == "__main__":
    bot.run(secret.TOKEN)
