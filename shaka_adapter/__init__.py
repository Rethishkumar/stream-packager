import logger
from string import Template
import subprocess

LOG = logger.get_logger(__name__)


PACKAGER_PATH = '/Users/rnair/shaka/packager-osx'


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
