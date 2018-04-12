
import logger
import BaseHTTPServer
from handler import RequestHandler
from SocketServer import ThreadingMixIn

LOG = logger.get_logger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""


class PackagingServer:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        BaseHTTPServer.HTTPServer.allow_reuse_address = True

    def start(self):
        self.httpd = ThreadedHTTPServer((self.ip, self.port),
                                        RequestHandler)
        self.httpd.serve_forever()
        LOG.info('started server on port %d', self.port)

    def stop(self):
        self.httpd.server_close()
        LOG.info('server stopped')
