import re
import logger
from shaka_adapter import ShakaAdapter
from fetcher import Fetcher

LOG = logger.get_logger(__name__)

segment_headers = {
    'Content-Type': 'application/dash+xml',
    'Access-Control-Allow-Headers': 'origin,range,accept-encoding,referer',
    'Access-Control-Allow-Methods': 'GET,HEAD,OPTIONS',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Expose-Headers': 'Server,range,Content-Length,Content-Range,Date'
}

PREPROCESSING_DIR_PATH = '/Volumes/RAMDisk/segments'

class SegmentPackager:

    def __init__(self):
        return

    def resolve_path(self, path):
        PATTERN = '/dash-package/live/(?P<stream_id>[-\w]+)/(?P<event_id>[-\w/]+)/' \
        '(?P<extension>[-\w/]+)/(?P<media_type>[-\w/]+)/(?P<filename>[-\w/]+).m4s'

        m = re.match(PATTERN, path)

        if m is None:
            LOG.warning('invalid uri %s', path)
            raise KeyError('invalid segment path %s', path)

        stream_id = m.group('stream_id')
        event_id = m.group('event_id')
        extension = m.group('extension')
        media_type = m.group('media_type')
        filename = m.group('filename')


        LOG.info('stream id: %s event id: %s media_type: %s filename: %s extension: %s',
                 stream_id, event_id, media_type, filename, extension)
        return (stream_id, event_id, media_type, filename, extension)

    def handle_request(self, path, headers):

        try:
            stream_id, event_id, media_type, filename, extension = self.resolve_path(path)
        except KeyError as e:
            LOG.warning(e.message)
            return (404, segment_headers, 'Invalid path')

        if 'init' == filename:
            # Initialization Segment Request
            content = self.get_initialization_segment(
                stream_id, event_id, media_type)
            return (200, segment_headers, content)

        uri = 'http://l2voddemo.akamaized.net/hls/live/%s/%s/%s.%s' % (
            stream_id, event_id, filename, extension)
        input_segment_path = '%s/%s_%s.%s' % (
            PREPROCESSING_DIR_PATH, filename, media_type, extension)

        Fetcher().fetch_and_write(uri, input_segment_path)
        content = ShakaAdapter().package_segment(
            input_segment_path, media_type)

        return (200, segment_headers, content)

    def get_initialization_segment(self, stream_id, event_id, media_type):

        if media_type == 'audio':
            filename = '644624_l2vclip77_master_700.m3u8_audio_init.mp4'
        elif media_type == 'video':
            filename = '644624_l2vclip77_master_700.m3u8_video_init.mp4'

        with open('/tmp/preprocess/' + filename, 'r') as fd:
            content = fd.read()
        return content


