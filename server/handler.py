import BaseHTTPServer
import threading
import logger

LOG = logger.get_logger('server')


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def log_message(self, _format, *args):
        LOG.info(_format % args)

    def do_GET(self):
        LOG.info('received GET')
        self.send_response(200)
        self.end_headers()
        message = threading.currentThread().getName()
        self.wfile.write(message)
        self.wfile.write('\n')
        return
