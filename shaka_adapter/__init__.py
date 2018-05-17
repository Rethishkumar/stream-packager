import os
import logger
from lxml import etree
from string import Template
import subprocess
from utils import delete_file

LOG = logger.get_logger(__name__)


PACKAGER_PATH = '/Users/rnair/shaka/packager-osx'
namespace = '{urn:mpeg:dash:schema:mpd:2011}'

class ShakaAdapter:

    def execute_cmd(self, cmd):

        LOG.debug('executing command %s', cmd)

        return_code = 0
        try:
            subprocess.check_output(cmd, shell=True,
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            LOG.exception(str(e))
            return_code = e.return_code

        return return_code

    def generate_mpd(
            self,
            audio_in_file, audio_out_init_file, audio_out_template,
            video_in_file, video_out_init_file, video_out_template,
            manifest_out_file):

        cmd_template = Template("""${packager} 'input=${audio_in_file},stream=audio,init_segment=${audio_out_init_file},segment_template=${audio_out_template}' 'input=${video_in_file},stream=video,init_segment=${video_out_init_file},segment_template=${video_out_template}' --mpd_output ${manifest_out_file} """)

        cmd = cmd_template.substitute({
            'packager': PACKAGER_PATH,
            'audio_in_file': audio_in_file,
            'audio_out_init_file': audio_out_init_file,
            'audio_out_template': audio_out_template,
            'video_in_file': video_in_file,
            'video_out_init_file': video_out_init_file,
            'video_out_template': video_out_template,
            'manifest_out_file': manifest_out_file})

        self.execute_cmd(cmd)

        return

    def package_segment(self, input_file, media_type):

        #~/shaka/packager-osx 'in=/tmp/master_700_215545.ts,stream=audio,out=/tmp/master_700_215545.mp4' --mpd_output 1.mpd
        cmd_template = Template("""${packager} 'in=${input_file},stream=${media_type},out=${out_file}' --mpd_output  ${manifest_out_file}""")

        params = {
            'packager': PACKAGER_PATH,
            'input_file': input_file,
            'media_type': media_type,
            'out_file': '%s.%s.%s.mp4' % (input_file, media_type, 'out'),
            'manifest_out_file': '%s.%s.%s' % (input_file, media_type, 'mpd')}

        cmd = cmd_template.substitute(**params)
        self.execute_cmd(cmd)

        mpd = etree.parse(params['manifest_out_file'])
        elem_segmentbase = mpd.find(namespace + 'Period').find(namespace + 'AdaptationSet').find(namespace + 'Representation').find(namespace + 'SegmentBase')
        byte_range = elem_segmentbase.get('indexRange').split('-')
        LOG.debug('reading bytes %s to %s', byte_range[0], byte_range[1])

        with open(params['out_file'], 'r') as fd:
            fd.seek(int(byte_range[0]) - 1)
            content = fd.read()

        with open(params['out_file'] + 'm4s', 'w') as fd:
            fd.write(content)
        #os.remove(params['out_file'])
        #os.remove(params['manifest_out_file'])
        return content
