import json

class Config:
    ADMIN_ROLE = 'admin_role'
    BOT_ADMIN_CHANNEL = 'bot_admin_channel'
    BOT_PUBLIC_CHANNEL = 'bot_public_channel'
    CLAN_NAME = 'clan_name'
    SOTW_NUMBER = 'SOTW_number'
    SOTW_TITLE = 'SOTW_title'
    GUILD_STATUS = 'status'
    PERMISSION_ERROR_MESSAGE = 'You lack the required role to interact with this bot.'

    #Sotw status values
    SOTW_NONE_PLANNED = 'sotw_none_planned'
    SOTW_POLL_OPENED = 'sotw_poll_opened'
    SOTW_POLL_CLOSED = 'sotw_poll_closed'
    SOTW_SCHEDULED = 'sotw_scheduled'
    SOTW_IN_PROGRESS = 'sotw_in_progress'
    SOTW_CONCLUDED = 'sotw_concluded'
    SOTW_PARTICIPANTS = 'sotw_participants'

    # Poll
    POLL_REACTIONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    POLL_CONTENT = 'This is some testing poll content.\n'
    CURRENT_POLL = 'current_poll_id'
    SKILLS_BEING_POLLED = 'skills_being_polled'
    POLL_WINNER = 'poll_winner'

    def __init__(self):
        with open('./config/config.json', 'r') as configFile:
            self.configs = json.load(configFile)

    def save(self):
        with open('./config/config.json', 'w') as configFile:
            json.dump(self.configs, configFile)

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

    def getGuildPublicChannel(self, guild):
        return guild.get_channel(self.get(guild.id, self.BOT_PUBLIC_CHANNEL))

    def getGuildAdminChannel(self, guild):
        return guild.get_channel(self.get(guild.id, self.BOT_ADMIN_CHANNEL))