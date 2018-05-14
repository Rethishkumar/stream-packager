import re
import m3u8
import logger
from fetcher import Fetcher
from fetcher import FetchError
from pre_processor import PreProcessor


LOG = logger.get_logger(__name__)

DASH_URI_PATTERN = '/dash-package/live/(?P<stream_id>[-\w]+)/(?P<event_id>[-\w/]+)/(?P<extension>[-\w/]+)/(?P<filename>[-\w]+).mpd'

class PackagingError(Exception):
    pass


class ManifestPackagingManager:

    def __init__(self):
        self.preprocessor = PreProcessor()
        pass

    def resolve_path(self, path):
        m = re.match(DASH_URI_PATTERN, path)

        if m is None:
            LOG.warning('invalid uri %s', path)
            raise KeyError('invalid manifest path %s', path)

        stream_id = m.group('stream_id')
        event_id = m.group('event_id')
        filename = m.group('filename')
        extension = m.group('extension')

        LOG.info('stream id: %s event id: %s filename: %s extension: %s',
                 stream_id, event_id, filename, extension)
        return (stream_id, event_id, filename, extension)

    def handle_request(self, path, headers):

        try:
            stream_id, event_id, filename, extension = self.resolve_path(path)
        except KeyError as e:
            LOG.warning(e.message)
            return (404, None, None)

        base_uri = 'http://l2voddemo.akamaized.net/hls/live/%s/%s' % (
            stream_id, event_id)

        master_manifest_url = '%s/%s.%s' % (base_uri,
                                            filename,
                                            extension)
        master_playlist = m3u8.loads(
            Fetcher().fetch(master_manifest_url))
        LOG.debug('master media %s', master_playlist.media)

        # Fetch the media playlist and process them
        playlists = {}
        for playlist in master_playlist.playlists:
            LOG.debug('playlist uri %s',
                      playlist.uri)

            playlists[playlist.uri] = m3u8.loads(
                Fetcher().fetch(
                    '%s/%s' % (base_uri,
                               playlist.uri)))

            playlists[playlist.uri].uri = playlist.uri

            # Preprocess the Playlist if not done before
            self.preprocessor.preprocess_playlist(
                stream_id, event_id,
                base_uri,
                playlists[playlist.uri])

        return (200, None, '%s %s %s' % (stream_id, event_id, filename))







