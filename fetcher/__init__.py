import logger
import requests

LOG = logger.get_logger(__name__)


class FetchError(Exception):
    pass


class Fetcher:

    def __init__(self):
        return

    def fetch(self, url):

        content = self.send_request(url)
        LOG.debug(content)
        return content

    def fetch_and_write(self, url, write_file):
        content = self.send_request(url)
        with open(write_file, 'w') as fd:
            fd.write(content)
        LOG.debug('written %d bytes to %s',
                  len(content), write_file)
        return

    def send_request(self, url):
        r = requests.get(url)
        if r.status_code != 200:
            LOG.info('%s fetch failed. status_code %d %s %s',
                     r.url, r.status_code, r.headers, r.content)
            raise FetchError('%s fetch failed. status_code %d %s %s' %
                             (r.url, r.status_code, r.headers, r.content))
        return r.content
