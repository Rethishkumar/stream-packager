import logger
from utils import singleton
from fetcher import Fetcher
from fetcher import FetchError

LOG = logger.get_logger(__name__)


@singleton
class PreProcessor:

    def __init__(self):
        self.pre_processing_dir = '/tmp'
        return

    def is_pre_processing_info_present(self, base_uri, media_playlist):
        return False

    def get_preprocessed_mpd(self, stream_id,
                             event_id, base_uri, media_playlist):

        if self.is_pre_processing_info_present(base_uri, media_playlist):
            return

        Fetcher().fetch_and_write(
            '%s/%s' % (base_uri, media_playlist.segments[0].uri),
            '%s/%s' % (
                self.pre_processing_dir, media_playlist.segments[0].uri))
        return
