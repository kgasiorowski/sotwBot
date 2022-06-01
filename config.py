import json

class Config:
    ADMIN_ROLE = 'adminRole'
    BOT_CHANNEL = 'botChannel'
    PERMISSION_ERROR_MESSAGE = 'You lack the required role to interact with this bot.'

    def __init__(self):
        with open('config.json', 'r') as configFile:
            self.configs = json.load(configFile)

    def save(self):
        with open('config.json', 'w') as configFile:
            json.dump(self.configs, configFile)

    def set(self, guildId: str, key, value):
        guildId = str(guildId)
        self.configs.setdefault(guildId, {})
        self.configs[guildId][key] = value
        self.save()

    def get(self, guildId: str, key):
        guildId = str(guildId)
        if guildId not in self.configs or key not in self.configs[guildId]:
            return None
        else:
            return self.configs[guildId][key]