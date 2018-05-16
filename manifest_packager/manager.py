import re
import m3u8
from time import gmtime
import logger
from fetcher import Fetcher
from fetcher import FetchError
from lxml import etree
from pre_processor import PreProcessor
from utils import cast_to_duration, extract_segment_number, format_time


LOG = logger.get_logger(__name__)

namespace = '{urn:mpeg:dash:schema:mpd:2011}'


manifest_headers = {
    'Content-Type': 'application/dash+xml',
    'Access-Control-Allow-Headers': 'origin,range,accept-encoding,referer',
    'Access-Control-Allow-Methods': 'GET,HEAD,OPTIONS',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Expose-Headers': 'Server,range,Content-Length,Content-Range,Date'
}

class PackagingError(Exception):
    pass


class ManifestPackagingManager:

    def __init__(self):
        #self.preprocessor = PreProcessor()
        pass

    def resolve_path(self, path):

        DASH_URI_PATTERN = '/dash-package/live/(?P<stream_id>[-\w]+)/' \
        '(?P<event_id>[-\w/]+)/(?P<extension>[-\w/]+)/(?P<filename>[-\w]+).mpd'
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

        # Fetch the media playlist and process them
        playlists = {}
        for playlist in master_playlist.playlists:
            LOG.debug('playlist uri %s',
                      playlist.uri)

            playlists[playlist.uri] = m3u8.loads(
                Fetcher().fetch(
                    '%s/%s' % (base_uri,
                               playlist.uri)))
            LOG.debug(
                'last segment in playlist %s PDT %s',
                playlists[playlist.uri].segments[-1],
                playlists[playlist.uri].segments[-1].program_date_time)

            playlists[playlist.uri].uri = playlist.uri

            # Preprocess the Playlist if not done before
            PreProcessor().preprocess_playlist(
                stream_id, event_id,
                base_uri,
                playlists[playlist.uri])

        mpd = self.generate_mpd(
            stream_id, event_id, master_playlist, playlists)

        return (200, manifest_headers, mpd)

    def generate_mpd(self, stream_id, event_id, master_playlist, playlists):

        done = False

        now_time = format_time(gmtime())

        for playlist_uri in playlists:
            if done:
                break
            done = True

            playlist = playlists[playlist_uri]

            manifest = etree.fromstring(
                PreProcessor().get_manifest(stream_id, event_id, playlist_uri))
            new_mpd = etree.fromstring(
                PreProcessor().get_manifest(stream_id, event_id, playlist_uri))
            #LOG.debug('original manifest \n%s', etree.tostring(new_mpd))
            segment = PreProcessor().get_reference_segment(
                stream_id, event_id, playlist_uri)

            elem_mpd = new_mpd
            elem_mpd.set(
                'publishTime', now_time)

            elem_mpd.set(
                'minBufferTime',
                cast_to_duration(playlist.target_duration * 2))
            elem_mpd.set(
                'minimumUpdatePeriod',
                cast_to_duration(playlist.target_duration))
            elem_mpd.set(
                'timeShiftBufferDepth',
                cast_to_duration(
                    playlist.target_duration * len(playlist.segments)))

            elem_period = new_mpd.find(namespace + 'Period')
            for elem_adaptation_set in elem_period.findall(namespace + 'AdaptationSet'):

                elem_baseurl = etree.Element('BaseURL')
                elem_baseurl.text = 'http://127.0.0.1:8881/dash-package/live/644624/l2vclip77/ts/'
                elem_adaptation_set.insert(0, elem_baseurl)

                contentType = elem_adaptation_set.get('contentType')

                elem_role = etree.Element('Role')
                elem_role.set('schemeIdUri', 'urn:mpeg:dash:role:2011')
                elem_role.set('value', 'main')
                elem_adaptation_set.insert(1, elem_role)

                elem_segment_template = elem_adaptation_set.find(
                    namespace + 'Representation').find(namespace + 'SegmentTemplate')
                elem_segment_template.set('initialization', '%s/init.m4s' % (contentType))
                elem_segment_template.set('media', '%s/master_700_$Number$.m4s' % (contentType))
                elem_segment_template.set('startNumber', extract_segment_number(segment.uri))
                elem_segment_template.set(
                    'presentationTimeOffset',
                    elem_segment_template.find(namespace + 'SegmentTimeline').find(namespace + 'S').get('t'))
                elem_segment_template.set('duration', str(2 * 90000))

                elem_segment_template.remove(elem_segment_template.find(namespace + 'SegmentTimeline'))

            elem_UTCTiming = etree.Element('UTCTiming')
            elem_UTCTiming.set('schemeIdUri', 'urn:mpeg:dash:utc:direct:2014')
            elem_UTCTiming.set('value', now_time)
            new_mpd.append(elem_UTCTiming)


            new_mpd_str = etree.tostring(new_mpd, pretty_print=True,
                                         xml_declaration=True,
                                         encoding='UTF-8')
            #LOG.info('new_mpd_str \n%s', new_mpd_str)
            return new_mpd_str














