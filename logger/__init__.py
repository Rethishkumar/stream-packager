
import logging


def config_logger():

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    logging.basicConfig(level=logging.DEBUG)
    fh = logging.FileHandler('packager.log')
    fh.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-8s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.info('logger initialized')


def get_logger(_logger):
    return logging.getLogger(_logger)
