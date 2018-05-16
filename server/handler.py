import logger
import threading
import BaseHTTPServer
# import manifest_packager.manager
from manifest_packager.manager import ManifestPackagingManager

LOG = logger.get_logger(__name__)


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def log_message(self, _format, *args):
        LOG.info(_format % args)

    def do_GET(self):

        if self.path[-len('.m4s'):] == '.m4s':
            status_code = 200
            body = 'received segment request'
        elif self.path[-len('.mpd'):] == '.mpd':
            mpm = ManifestPackagingManager()
            status_code, headers, body = mpm.handle_request(
                self.path, self.headers)

        self.send_response(status_code)

        for header in headers:
            self.send_header(header, headers[header])

        self.end_headers()
        message = threading.currentThread().getName()
        if body is not None:
            self.wfile.write(body)
        else:
            self.wfile.write(message)
        self.wfile.write('\n')
        return
