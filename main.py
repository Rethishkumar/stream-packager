import sys
import logger
from time import sleep
from server import PackagingServer as Server

LOG = logger.get_logger(__name__)


def main():

    sys.path.append('/Users/rnair/github/stream-packager/')
    logger.config_logger()
    server = Server('127.0.0.1', 8881)
    server.start()

    try:
        while (1):
            sleep(10)
    except KeyboardInterrupt:
        server.stop()

    return


if __name__ == "__main__":
    main()
