
import logging


def config_logger():
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(level=logging.INFO,
                        filename='packager.log',
                        format=FORMAT)


def get_logger(_logger):
    return logging.getLogger(_logger)
