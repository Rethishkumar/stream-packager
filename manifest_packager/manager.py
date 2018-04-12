import re
import m3u8
import logger
from fetcher import Fetcher
from fetcher import FetchError


LOG = logger.get_logger(__name__)

DASH_URI_PATTERN = '/dash/live-packaging/(?P<stream_id>[-\w]+)/(?P<event_id>[-\w/]+)/(?P<file_name>[-\w]+).mpd'

class PackagingError(Exception):
    pass

class ManifestPackagingManager:

    def extract_path_info(self, path):
        m = re.match(DASH_URI_PATTERN, path)

        if m is None:
            raise KeyError('invalid manifest path %s', path)

        self.stream_id = m.group('stream_id')
        self.event_id = m.group('event_id')
        self.filename = m.group('file_name')

        LOG.info('stream id: %s event id: %s filename: %s',
                 self.stream_id, self.event_id, self.filename)

    def handle_request(self, path, headers):

        try:
            self.extract_path_info(path)
        except KeyError as e:
            LOG.warning(e.message)
            return (404, None, None)


        # fetch the master
        status_code, headers, content = Fetcher()

        return (200, None, '%s %s %s' % (self.stream_id, self.event_id, self.filename))


    def fetch_playlists(self):

        master_playlist_content = self.fetch_master_playlist()

        self.master = m3u8.loads(master_playlist_content)
        # This should actually be is master
        if not self.master.is_variant:









    def fetch_master_playlist(self):

        path = '/hls/live/{}/{}/{}.m3u8'.format(
            self.stream_id, self.event_id, self.filename)

        return Fetcher(path, self)
