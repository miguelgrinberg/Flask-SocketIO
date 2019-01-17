import asyncio
import sys
from urllib.parse import urlsplit

try:
    import tornado.web
    import tornado.websocket
except ImportError:  # pragma: no cover
    pass
import six


def get_tornado_handler(engineio_server):
    class Handler(tornado.websocket.WebSocketHandler):  # pragma: no cover
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.receive_queue = asyncio.Queue()

        async def get(self):
            if self.request.headers.get('Upgrade', '').lower() == 'websocket':
                super().get()
            await engineio_server.handle_request(self)

        async def post(self):
            await engineio_server.handle_request(self)

        async def options(self):
            await engineio_server.handle_request(self)

        async def on_message(self, message):
            await self.receive_queue.put(message)

        async def get_next_message(self):
            return await self.receive_queue.get()

        def on_close(self):
            self.receive_queue.put_nowait(None)

    return Handler


def translate_request(handler):
    """This function takes the arguments passed to the request handler and
    uses them to generate a WSGI compatible environ dictionary.
    """
    class AwaitablePayload(object):
        def __init__(self, payload):
            self.payload = payload or b''

        async def read(self, length=None):
            if length is None:
                r = self.payload
                self.payload = b''
            else:
                r = self.payload[:length]
                self.payload = self.payload[length:]
            return r

    payload = handler.request.body

    uri_parts = urlsplit(handler.request.path)
    full_uri = handler.request.path
    if handler.request.query:  # pragma: no cover
        full_uri += '?' + handler.request.query
    environ = {
        'wsgi.input': AwaitablePayload(payload),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.async': True,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'SERVER_SOFTWARE': 'aiohttp',
        'REQUEST_METHOD': handler.request.method,
        'QUERY_STRING': handler.request.query or '',
        'RAW_URI': full_uri,
        'SERVER_PROTOCOL': 'HTTP/%s' % handler.request.version,
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_PORT': '0',
        'SERVER_NAME': 'aiohttp',
        'SERVER_PORT': '0',
        'tornado.handler': handler
    }

    for hdr_name, hdr_value in handler.request.headers.items():
        hdr_name = hdr_name.upper()
        if hdr_name == 'CONTENT-TYPE':
            environ['CONTENT_TYPE'] = hdr_value
            continue
        elif hdr_name == 'CONTENT-LENGTH':
            environ['CONTENT_LENGTH'] = hdr_value
            continue

        key = 'HTTP_%s' % hdr_name.replace('-', '_')
        environ[key] = hdr_value

    environ['wsgi.url_scheme'] = environ.get('HTTP_X_FORWARDED_PROTO', 'http')

    path_info = uri_parts.path

    environ['PATH_INFO'] = path_info
    environ['SCRIPT_NAME'] = ''

    return environ


def make_response(status, headers, payload, environ):
    """This function generates an appropriate response object for this async
    mode.
    """
    tornado_handler = environ['tornado.handler']
    tornado_handler.set_status(int(status.split()[0]))
    for header, value in headers:
        tornado_handler.set_header(header, value)
    tornado_handler.write(payload)
    tornado_handler.finish()


class WebSocket(object):  # pragma: no cover
    """
    This wrapper class provides a tornado WebSocket interface that is
    somewhat compatible with eventlet's implementation.
    """
    def __init__(self, handler):
        self.handler = handler
        self.tornado_handler = None

    async def __call__(self, environ):
        self.tornado_handler = environ['tornado.handler']
        self.environ = environ
        await self.handler(self)

    async def close(self):
        self.tornado_handler.close()

    async def send(self, message):
        self.tornado_handler.write_message(
            message, binary=isinstance(message, bytes))

    async def wait(self):
        msg = await self.tornado_handler.get_next_message()
        if not isinstance(msg, six.binary_type) and \
                not isinstance(msg, six.text_type):
            raise IOError()
        return msg


_async = {
    'asyncio': True,
    'translate_request': translate_request,
    'make_response': make_response,
    'websocket': sys.modules[__name__],
    'websocket_class': 'WebSocket'
}
