import json

class Config:
    COMMAND_PREFIX = 'command_prefix'
    ADMIN_ROLE = 'admin_role'
    BOT_ADMIN_CHANNEL = 'bot_admin_channel'
    BOT_PUBLIC_CHANNEL = 'bot_public_channel'
    CLAN_NAME = 'clan_name'
    SOTW_NUMBER = 'SOTW_number'
    SOTW_TITLE = 'SOTW_title'
    GUILD_STATUS = 'status'
    PERMISSION_ERROR_MESSAGE = 'You lack the required role to interact with this bot.'
    ADMIN_GUIDE_MESSAGE_IDS = 'admin_guide_message_ids'
    ADMIN_GUIDE_MESSAGE_CONTENT = 'This eventually will be the admin help message'
    SOTW_SKILLS = ['agility',
                   'construction',
                   'cooking',
                   'crafting',
                   'farming',
                   'firemaking',
                   'fishing',
                   'fletching',
                   'herblore',
                   'hunting',
                   'mining',
                   'prayer',
                   'ranged',
                   'runecrafting',
                   'slayer',
                   'smithing',
                   'thieving',
                   'woodcutting']

    #Sotw status values
    SOTW_NONE_PLANNED = 'sotw_none_planned'
    SOTW_POLL_OPENED = 'sotw_poll_opened'
    SOTW_POLL_CLOSED = 'sotw_poll_closed'
    SOTW_SCHEDULED = 'sotw_scheduled'
    SOTW_IN_PROGRESS = 'sotw_in_progress'
    SOTW_CONCLUDED = 'sotw_concluded'
    SOTW_PARTICIPANTS = 'participants'
    SOTW_COMPETITION_ID = 'sotw_id'
    SOTW_START_DATE = 'sotw_start_date'
    SOTW_END_DATE = 'sotw_end_date'
    SOTW_VERIFICATION_CODE = 'sotw_verification_code'
    SOTW_WINNER_DM_ID = 'sotw_winner_dm_id'

    # Groups
    WOM_GROUP_ID = 'wom_group_id'
    WOM_GROUP_VERIFICATION_CODE = 'wom_group_verification_code'

    # Poll
    POLL_REACTIONS_NUMERICAL = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    POLL_REACTIONS_ALPHABETICAL = [chr(i) for i in range(127462, 127462+26)]
    POLL_CONTENT = 'This is some testing poll content.\n'
    CURRENT_POLL = 'current_poll_id'
    SKILLS_BEING_POLLED = 'skills_being_polled'
    SOTW_PREVIOUS_SKILL = 'sotw_previous_skill'
    POLL_WINNER = 'poll_winner'

    def __init__(self):
        self.load()

    def save(self):
        with open('./config/config.json', 'w') as configFile:
            json.dump(self.configs, configFile)

    def load(self):
        with open('./config/config.json', 'r') as configFile:
            self.configs = json.load(configFile)

    def set(self, guildId: str, key, value):
        guildId = str(guildId)
        self.configs.setdefault(guildId, {})
        self.configs[guildId][key] = value
        self.save()

    def get(self, guildId: str, key):
        guildId = str(guildId)
        self.configs.setdefault(guildId, {})
        if key not in self.configs[guildId]:
            return None
        else:
            return self.configs[guildId][key]

    def addParticipant(self, guildId: str, username: str, userDiscordId: int):
        guildId = str(guildId)
        self.configs.setdefault(guildId, {})
        self.configs[guildId].setdefault('participants', {})
        for participant in list(self.configs[guildId]['participants'].keys()):
            if self.configs[guildId]['participants'][participant] == userDiscordId:
                del self.configs[guildId]['participants'][participant]
        self.configs[guildId]['participants'][username] = userDiscordId
        self.save()

    def getParticipant(self, guildId: str, username: str):
        guildId = str(guildId)

        if guildId not in self.configs:
            return None

        if 'participants' not in self.configs[guildId]:
            return None

        if username not in self.configs[guildId]['participants']:
            return None

        return self.configs[guildId]['participants'][username];


    def getParticipantList(self, guildId: str):
        guildId = str(guildId)
        participants = self.get(guildId, self.SOTW_PARTICIPANTS)
        if participants is None:
            return None
        return list(participants.keys())

    def getGuildPublicChannel(self, guild):
        return guild.get_channel(self.get(guild.id, self.BOT_PUBLIC_CHANNEL))

    def getGuildAdminChannel(self, guild):
        return guild.get_channel(self.get(guild.id, self.BOT_ADMIN_CHANNEL))

    def getGuildByDmId(self, userDmId: str):
        for key in self.configs.keys():
            data = self.configs[key]
            if self.SOTW_WINNER_DM_ID not in data:
                continue
            if data[self.SOTW_WINNER_DM_ID] == userDmId:
                return key