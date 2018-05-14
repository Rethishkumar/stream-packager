import os
import logging


def config_logger():

    os.environ['TZ'] = 'UTC'
    logFormatter = logging.Formatter(
        '%(asctime)s::%(thread)d::%(name)-4s::%(levelname)s::%(message)s')
    rootLogger = logging.getLogger()
    logging.basicConfig(level=logging.DEBUG)

    fileHandler = logging.FileHandler('packager.log')
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)

    rootLogger.info('logger initialized')

def get_logger(_logger):
    return logging.getLogger(_logger)
