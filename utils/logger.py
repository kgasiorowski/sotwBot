import logging
import logging.config

logger = None

def getLogger():
    global logger
    if logger is None:
        logger = initLogger()
    return logger

def initLogger():
    logger = logging.getLogger('newbs_bot')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setStream(open('./logs/logfile.log', 'a'))

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger