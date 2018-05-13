import re
import m3u8
import logger
from fetcher import Fetcher
from fetcher import FetchError
from pre_processor import PreProcessor


LOG = logger.get_logger(__name__)

DASH_URI_PATTERN = '/dash-package/live/(?P<stream_id>[-\w]+)/(?P<event_id>[-\w/]+)/(?P<extension>[-\w/]+)/(?P<file_name>[-\w]+).mpd'

class PackagingError(Exception):
    pass


class ManifestPackagingManager:

    def extract_path_info(self, path):
        m = re.match(DASH_URI_PATTERN, path)

        if m is None:
            LOG.warning('invalid uri %s', path)
            raise KeyError('invalid manifest path %s', path)

        self.stream_id = m.group('stream_id')
        self.event_id = m.group('event_id')
        self.filename = m.group('file_name')
        self.extension = m.group('extension')

        self.pre_processor = PreProcessor()

        LOG.info('stream id: %s event id: %s filename: %s extension: %s',
                 self.stream_id, self.event_id, self.filename, self.extension)

    def handle_request(self, path, headers):

        try:
            self.extract_path_info(path)
        except KeyError as e:
            LOG.warning(e.message)
            return (404, None, None)

        self.base_uri = 'http://l2voddemo.akamaized.net/hls/live/%s/%s' % (
            self.stream_id, self.event_id)

        master_manifest_url = '%s/%s.%s' % (self.base_uri,
                                            self.filename,
                                            self.extension)
        master_playlist = m3u8.loads(
            Fetcher().fetch(master_manifest_url))
        LOG.debug('master media %s', master_playlist.media)

        # Fetch the media playlist and process them
        playlists = {}
        for playlist in master_playlist.playlists:
            LOG.debug('playlist uri %s base_uri %s',
                      playlist.uri, playlist.base_uri)

            playlists[playlist.uri] = m3u8.loads(
                Fetcher().fetch(
                    '%s/%s' % (self.base_uri,
                               playlist.uri)))

            # Preprocess the Playlist if not done before
            PreProcessor().get_preprocessed_mpd(
                self.stream_id, self.event_id,
                self.base_uri, playlists[playlist.uri])

        return (200, None, '%s %s %s' % (self.stream_id, self.event_id, self.filename))
