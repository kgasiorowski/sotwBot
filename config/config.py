import json

class Config:
    ADMIN_ROLE = 'admin_role'
    BOT_ADMIN_CHANNEL = 'bot_admin_channel'
    BOT_PUBLIC_CHANNEL = 'bot_public_channel'
    CLAN_NAME = 'clan_name'
    SOTW_NUMBER = 'SOTW_number'
    GUILD_STATUS = 'status'
    PERMISSION_ERROR_MESSAGE = 'You lack the required role to interact with this bot.'

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