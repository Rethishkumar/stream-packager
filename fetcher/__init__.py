import logger
import requests

LOG = logger.get_logger(__name__)


class FetchError(Exception):
    pass


class Fetcher:

    def __init__(self, url, requester):
        self.url = url
        self.requester = requester

    def fetch(self):
        r = requests.get(self.url)
        if r.status_code != 200:
            LOG.info('%s fetch failed. status_code %d %s %s',
                     r.url, r.status_code, r.headers, r.content)
            raise FetchError('%s fetch failed. status_code %d %s %s' %
                             (r.url, r.status_code, r.headers, r.content))
        else:
            LOG.info('%s fetch success. status_code %d %s %s',
                     r.url, r.status_code, r.headers, r.content)

        return r.content
        # self.requester.handle_response(self.requester,
        #                                r.status_code,
        #                                r.headers,
        #                                r.content)
