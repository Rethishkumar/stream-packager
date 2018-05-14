from lxml import etree
import logger
import pickle
from utils import singleton
from fetcher import Fetcher
from string import Template
from shaka_adapter import ShakaAdapter

LOG = logger.get_logger(__name__)

PREPROCESSING_DIR_PATH = '/tmp'


class PlaylistInfo:
    def __init__(self, playlist_uri):
        self._playlist_uri = playlist_uri
        self._program_date_time = None
        self._manifest = None
        return

    @property
    def playlist_uri(self):
        return self._playlist_uri

    @property
    def program_date_time(self):
        return self._program_date_time

    @program_date_time.setter
    def program_date_time(self, program_date_time):
        self._program_date_time = program_date_time

    @property
    def reference_segment(self):
        return self._reference_segment

    @reference_segment.setter
    def reference_segment(self, reference_segment):
        self._reference_segment = reference_segment

    @property
    def manifest(self):
        return self._manifest

    @manifest.setter
    def program_date_time(self, manifest):
        self._manifest = manifest

    def save_to_disk(self, stream_id, event_id):
        picke_path = '%s/%s_%s_%s_pickle.dat' % (
            PREPROCESSING_DIR_PATH,
            stream_id, event_id, self._playlist_uri)

        with open(picke_path, 'wb') as fd:
            pickle.dump(self, fd)

        return


class StreamInfo:

    def __init__(self, stream_id, event_id, base_uri):
        self._stream_id = stream_id
        self._event_id = event_id
        self._base_uri = base_uri
        self.playlists = {}

    @property
    def stream_id(self):
        return self._stream_id

    @property
    def event_id(self):
        return self._event_id

    def get_init_path(self, playlist_uri, media_type):

        template_params = {
            'pre_processing_dir': PREPROCESSING_DIR_PATH,
            'stream_id': self._stream_id,
            'event_id': self._event_id,
            'playlist_uri': playlist_uri,
            'media_type': media_type
        }

        INIT_TEMPLATE = Template(
            '${pre_processing_dir}/${stream_id}_'
            '${event_id}_${playlist_uri}_${media_type}_init.mp4')

        return INIT_TEMPLATE.substitute(**template_params)

    def get_segment_path(self, playlist_uri, media_type):

        template_params = {
            'pre_processing_dir': PREPROCESSING_DIR_PATH,
            'stream_id': self._stream_id,
            'event_id': self._event_id,
            'playlist_uri': playlist_uri,
            'media_type': media_type
        }

        SEGMENT_TEMPLATE = Template(
            '${pre_processing_dir}/${stream_id}_'
            '${event_id}_${playlist_uri}_${media_type}_$Number$.m4s')

        return SEGMENT_TEMPLATE.safe_substitute(**template_params)

    def get_manifest_path(self, playlist_uri):

        template_params = {
            'pre_processing_dir': PREPROCESSING_DIR_PATH,
            'stream_id': self._stream_id,
            'event_id': self._event_id,
            'playlist_uri': playlist_uri
        }

        MANIFEST_TEMPLATE = Template(
            '${pre_processing_dir}/${stream_id}_'
            '${event_id}_${playlist_uri}.mpd')
        return MANIFEST_TEMPLATE.substitute(**template_params)

    def get_playlist_info(self, playlist_uri):
        if playlist_uri in self.playlists:
            LOG.debug('found playlist info in memory')
            return self.playlists[playlist_uri]

        obj = self.load_from_disk(playlist_uri)
        if obj is not None:
            self.playlists[playlist_uri] = obj

        return obj

    def load_from_disk(self, playlist_uri):

        pickle_path = '%s/%s_%s_%s_pickle.dat' % (
            PREPROCESSING_DIR_PATH,
            self._stream_id, self._event_id,
            playlist_uri)
        try:
            with open(pickle_path, 'r') as fd:
                obj = pickle.load(fd)
                LOG.debug('loaded preprocessed info for playlist %s PDT %s',
                          obj.playlist_uri,
                          obj.program_date_time)
                return obj
        except IOError:
            LOG.debug('picked file %s not found',
                      pickle_path)

        return None

    def preprocess_playlist(self, media_playlist):

        LOG.debug('preprocessing playlist %s',
                  media_playlist.uri)

        # use a segment from the middle as reference as
        # it's less likely to get expired when fetching
        reference_segment = media_playlist.segments[len(
            media_playlist.segments) // 2]

        input_segment_path = '%s/%s' % (
            PREPROCESSING_DIR_PATH,
            reference_segment.uri)

        Fetcher().fetch_and_write(
            '%s/%s' % (
                self._base_uri, reference_segment.uri),
            input_segment_path)

        manifest_path = self.get_manifest_path(media_playlist.uri)
        ShakaAdapter().generate_mpd(
            input_segment_path,
            self.get_init_path(media_playlist.uri, 'audio'),
            self.get_segment_path(media_playlist.uri, 'audio'),
            input_segment_path,
            self.get_init_path(media_playlist.uri, 'video'),
            self.get_segment_path(media_playlist.uri, 'video'),
            manifest_path)

        preprocessed_playlist = PlaylistInfo(
            media_playlist.uri)

        with open(manifest_path, 'r') as fd:
            preprocessed_playlist.manifest = fd.read()
            LOG.debug('got manifest %s: %s',
                      manifest_path,
                      preprocessed_playlist.manifest)

        preprocessed_playlist.program_date_time = \
            reference_segment.program_date_time

        preprocessed_playlist.save_to_disk(
            self._stream_id,
            self._event_id)

        self.playlists[media_playlist.uri] = \
            preprocessed_playlist
        return preprocessed_playlist


@singleton
class PreProcessor:

    def __init__(self):

        self.streams = {}
        return

    def preprocess_playlist(self, stream_id, event_id,
                            base_uri,
                            media_playlist):

        stream_info_str = '%s_%s' % (stream_id, event_id)
        if stream_info_str in self.streams:
            stream_info = self.streams[stream_info_str]
        else:
            stream_info = StreamInfo(
                stream_id, event_id, base_uri)
            self.streams[stream_info_str] = stream_info

        # Try loading from memory or Disk
        playlist_info = stream_info.get_playlist_info(
            media_playlist.uri)
        if playlist_info is not None:
            return

        self.streams[stream_info_str].preprocess_playlist(media_playlist)

        return









    # def find_common_segment(self, playlist, reference_segment):

    #     matching_segment = None
    #     try:
    #         for segment, idx in enumerate(playlist.segments):

    #             if (segment.program_date_time ==
    #                     reference_segment.program_date_time):
    #                 matching_segment = segment
    #                 break

    #             elif (playlist[idx + 1].program_date_time <=
    #                     reference_segment.program_date_time):
    #                 matching_segment = segment
    #                 break

    #             elif (segment.program_date_time >
    #                     reference_segment.program_date_time) and \
    #                 (playlist[idx + 1].program_date_time <
    #                     reference_segment.program_date_time):
    #                 matching_segment = segment
    #                 break
    #     except IndexError:
    #         LOG.error('segment matching %s not found in playlist %s.',
    #                   reference_segment.program_date_time,
    #                   playlist.uri)
    #         return None

    #     if matching_segment is not None:
    #         LOG.info('segment matching PDT %s found in playlist %s PDT %s',
    #                  reference_segment.program_date_time,
    #                  playlist.uri,
    #                  matching_segment.program_date_time)
    #     return None


