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

        return self.package_static(input_file, media_type)

    def package_static(self, input_file, media_type):

        #~/shaka/packager-osx 'in=/tmp/master_700_215545.ts,stream=audio,out=/tmp/master_700_215545.mp4' --mpd_output 1.mpd
        cmd_template = Template("""${packager} 'in=${input_file},stream=${media_type},out=${output_file}' --mpd_output  ${manifest_out_file}""")

        params = {
            'packager': PACKAGER_PATH,
            'input_file': input_file,
            'media_type': media_type,
            'output_file': '%s_self_init.mp4' % (input_file),
            'manifest_out_file': '%s.static.mpd' % (input_file)}

        cmd = cmd_template.safe_substitute(**params)
        self.execute_cmd(cmd)

        # Send the whole self initializing segment
        with open(params['output_file'], 'r') as fd:
            content = fd.read()
        return content


        mpd = etree.parse(params['manifest_out_file'])
        elem_SegmentBase = mpd.find(namespace + 'Period').find(
            namespace + 'AdaptationSet').find(
            namespace + 'Representation').find(
            namespace + 'SegmentBase')

        start_byte = int(elem_SegmentBase.get('indexRange').split('-')[0])
        with open(params['output_file'], 'r') as fd:
            fd.seek(start_byte)
            content = fd.read()


        if media_type == 'audio':
            styp_file = '/tmp/preprocess/styp.644624_l2vclip77_master_700.m3u8_audio_1.m4s'
        elif media_type == 'video':
            styp_file = '/tmp/preprocess/styp.644624_l2vclip77_master_700.m3u8_audio_1.m4s'

        with open(styp_file) as fd:
            styp_box = fd.read()

        with open(params['input_file'] + '.self.initializing.check.m4s', 'w') as fd:
            fd.write(styp_box)
            fd.write(content)
        #os.remove(params['out_file'])
        #os.remove(params['manifest_out_file'])
        return styp_box + content

    def package_with_template(self, input_file, media_type):

        #/Users/rnair/shaka/packager-osx 'in=/tmp/segments/master_700_264813_video.ts,stream=video,init_segment=/tmp/segments/master_700_264813_video_init.mp4,segment_template=/tmp//master_700_264813_video_$Number$.m4s' --mpd_output  /tmp/segments/master_700_264813_video.ts.mpd
        cmd_template = Template("""${packager} 'in=${input_file},stream=${media_type},init_segment=${init_segment},segment_template=${segment_template}' --mpd_output ${manifest_out_file}""")
        params = {
            'packager': PACKAGER_PATH,
            'input_file': input_file,
            'media_type': media_type,
            'init_segment': '%s_init.m4s' % (input_file),
            'segment_template': '%s_$Number$.m4s' % (input_file),
            'manifest_out_file': '%s.dynamic.mpd' % (input_file)}

        cmd = cmd_template.safe_substitute(**params)
        self.execute_cmd(cmd)

        mpd = etree.parse(params['manifest_out_file'])
        elem_SegmentTimeline = mpd.find(namespace + 'Period').find(
            namespace + 'AdaptationSet').find(
            namespace + 'Representation').find(
            namespace + 'SegmentTemplate').find(
            namespace + 'SegmentTimeline')

        content = None
        segment_number = 0
        for elem_s in elem_SegmentTimeline.findall(namespace + 'S'):
            num_segments = int(elem_s.get('r', 0)) + 1
            for i in range(num_segments):
                segment_number += 1
                filename = Template('%s_$Number.m4s' % (input_file)).safe_substitute({'Number': str(segment_number)})
                LOG.debug('reading segment %s', filename)

                with open(filename, 'r') as fd:
                    if content is None:
                        content = fd.read()
                        continue
                    content += fd.read()

        with open(params['input_file'] + '.fragment.check.m4s', 'w') as fd:
            fd.write(content)
        return content
