from discord.ext import commands
from utils import logger

class SOTWBot(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

        self.logger = logger.getLogger()

    async def on_command_error(self, context, exception):
        await commands.Bot.on_command_error(self, context, exception)
        self.logger.debug(str(exception.args[0]))
