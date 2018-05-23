from lxml import etree
import logger
import pickle
from utils import singleton
from fetcher import Fetcher
from string import Template
from utils import delete_file
from shaka_adapter import ShakaAdapter

LOG = logger.get_logger(__name__)

PREPROCESSING_DIR_PATH = '/Volumes/RAMDisk/preprocess'


class PlaylistInfo:
    def __init__(self, playlist_uri, reference_segment):
        self._playlist_uri = playlist_uri
        self._reference_segment = reference_segment
        self._manifest = None
        self._styp_box = {}
        return

    @property
    def playlist_uri(self):
        return self._playlist_uri

    @property
    def reference_segment(self):
        return self._reference_segment

    @property
    def manifest(self):
        return self._manifest

    @manifest.setter
    def manifest(self, manifest):
        self._manifest = manifest

    def get_styp_box(self, media_type):
        return self._styp_box[media_type]

    def set_styp_box(self, styp_box, media_type):
        self._styp_box[media_type] = styp_box

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

    def get_manifest(self, playlist_uri):
        return self.playlists[playlist_uri].manifest

    def get_reference_segment(self, playlist_uri):
        return self.playlists[playlist_uri].reference_segment

    def get_styp_box(self, playlist_uri, media_type):
        return self.playlists[playlist_uri].get_styp_box(media_type)

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

    def get_first_segment_path(self, playlist_uri, media_type):
        return self.get_segment_path(playlist_uri, media_type, str(1))

    def get_segment_path(self, playlist_uri, media_type, number='$Number$'):

        template_params = {
            'pre_processing_dir': PREPROCESSING_DIR_PATH,
            'stream_id': self._stream_id,
            'event_id': self._event_id,
            'playlist_uri': playlist_uri,
            'media_type': media_type,
            'number': number
        }

        SEGMENT_TEMPLATE = Template(
            '${pre_processing_dir}/${stream_id}_'
            '${event_id}_${playlist_uri}_${media_type}_${number}.m4s')

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

    def get_styp_path(self, playlist_uri, media_type):
        template_params = {
            'pre_processing_dir': PREPROCESSING_DIR_PATH,
            'stream_id': self._stream_id,
            'event_id': self._event_id,
            'playlist_uri': playlist_uri,
            'media_type': media_type
        }

        STYP_PATH_TEMPLATE = Template(
            '${pre_processing_dir}/${stream_id}_'
            '${event_id}_${playlist_uri}_${media_type}.styp.mp4')
        return STYP_PATH_TEMPLATE.substitute(**template_params)

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
                LOG.debug('loaded preprocessed info for playlist: %s '
                          'Reference Segment: %s PDT: %s',
                          obj.playlist_uri,
                          obj.reference_segment,
                          obj.reference_segment.program_date_time)
                return obj
        except IOError:
            LOG.debug('pickled file %s not found',
                      pickle_path)

        return None

    def preprocess_playlist(self, media_playlist):

        LOG.debug('preprocessing playlist %s',
                  media_playlist.uri)

        # use a segment from the middle as reference as
        # it's less likely to get expired when fetching
        reference_segment = self.find_common_segment(media_playlist)
        if reference_segment is None:
            # If no common segment found pick one from the middle of the list
            media_playlist.segments[len(media_playlist.segments) // 2]

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
            media_playlist.uri, reference_segment)

        # Read and save the manifest
        with open(manifest_path, 'r') as fd:
            preprocessed_playlist.manifest = fd.read()
            LOG.debug('got manifest %s: %s',
                      manifest_path,
                      preprocessed_playlist.manifest)

        delete_file(manifest_path)

        # Save the styp box
        for media_type in ['audio, video']:
            with open(self.get_first_segment_path(
                    media_playlist.uri, 'audio')) as fd:
                styp_box = fd.read(36)
                preprocessed_playlist.set_styp_box(styp_box, media_type)

        preprocessed_playlist.save_to_disk(
            self._stream_id,
            self._event_id)

        self.playlists[media_playlist.uri] = \
            preprocessed_playlist
        return preprocessed_playlist

    def find_common_segment(self, playlist):
        """
            Function to find the closest segment in time segment to the
            reference segment.
            Required to reduce a/v sync issues and seamless switching between
            renditions.
        """

        # get the lowest PDT
        reference_pdt = None
        for key in self.playlists:
            if reference_pdt is None:
                reference_pdt = self.playlists[key].reference_segment.program_date_time
                continue
            if reference_pdt < self.playlists[key].reference_segment.program_date_time:
                reference_pdt = self.playlists[key].reference_segment.program_date_time

        # if searching for first time use the one in the middle of the playlist
        if reference_pdt is None:
            # use a segment from the middle as reference as
            # it's less likely to get expired when fetching
            return playlist.segments[len(playlist.segments) // 2]

        matching_segment = None
        try:
            for idx, segment in enumerate(playlist.segments):

                #LOG.debug('matching %s against %s', segment.program_date_time, reference_pdt)
                if (segment.program_date_time == reference_pdt):
                    matching_segment = segment
                    break

                elif (playlist.segments[idx + 1].program_date_time == reference_pdt):
                    matching_segment = playlist.segments[idx + 1]
                    break

                elif (segment.program_date_time > reference_pdt) and \
                        (playlist.segments[idx + 1].program_date_time > reference_pdt):
                    matching_segment = segment
                    break
        except IndexError:
            LOG.error('segment matching %s not found in playlist %s.',
                      reference_pdt,
                      playlist.uri)
            return None

        if matching_segment is not None:
            LOG.info('segment matching PDT %s found in playlist %s PDT %s',
                     reference_pdt,
                     playlist.uri,
                     matching_segment.program_date_time)
        return matching_segment


@singleton
class PreProcessor:

    def __init__(self):

        self.streams = {}
        return

    def stream_key(self, stream_id, event_id):
        return '%s_%s' % (stream_id, event_id)

    def preprocess_playlist(self, stream_id, event_id,
                            base_uri,
                            media_playlist):

        stream_key = self.stream_key(stream_id, event_id)

        if stream_key in self.streams:
            stream_info = self.streams[stream_key]
        else:
            stream_info = StreamInfo(
                stream_id, event_id, base_uri)
            self.streams[stream_key] = stream_info

        # Try loading from memory or Disk
        playlist_info = stream_info.get_playlist_info(
            media_playlist.uri)
        if playlist_info is not None:
            return

        self.streams[stream_key].preprocess_playlist(media_playlist)

        return

    def get_manifest(self, stream_id, event_id, playlist_uri):
        stream_key = self.stream_key(stream_id, event_id)
        return self.streams[stream_key].get_manifest(playlist_uri)

    def get_reference_segment(self, stream_id, event_id, playlist_uri):
        stream_key = self.stream_key(stream_id, event_id)
        return self.streams[stream_key].get_reference_segment(playlist_uri)

    def get_styp_box(self, stream_id, event_id, playlist_uri, media_type):
        stream_key = self.stream_key(stream_id, event_id)
        return self.streams[stream_key].get_styp_box(playlist_uri, media_type)




