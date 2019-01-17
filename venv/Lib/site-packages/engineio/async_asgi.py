import sys


class ASGIApp:
    """ASGI application middleware for Engine.IO.

    This middleware dispatches traffic to an Engine.IO application. It can
    also serve a list of static files to the client, or forward unrelated
    HTTP traffic to another ASGI application.

    :param engineio_server: The Engine.IO server. Must be an instance of the
                            ``engineio.AsyncServer`` class.
    :param static_files: A dictionary where the keys are URLs that should be
                         served as static files. For each URL, the value is
                         a dictionary with ``content_type`` and ``filename``
                         keys. This option is intended to be used for serving
                         client files during development.
    :param other_asgi_app: A separate ASGI app that receives all other traffic.
    :param engineio_path: The endpoint where the Engine.IO application should
                          be installed. The default value is appropriate for
                          most cases.

    Example usage::

        import engineio
        import uvicorn

        eio = engineio.AsyncServer()
        app = engineio.ASGIApp(eio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'index.html'},
            '/index.html': {'content_type': 'text/html',
                            'filename': 'index.html'},
        })
        uvicorn.run(app, '127.0.0.1', 5000)
    """
    def __init__(self, engineio_server, other_asgi_app=None,
                 static_files=None, engineio_path='engine.io'):
        self.engineio_server = engineio_server
        self.other_asgi_app = other_asgi_app
        self.engineio_path = engineio_path.strip('/')
        self.static_files = static_files or {}

    def __call__(self, scope):
        if scope['type'] in ['http', 'websocket'] and \
                scope['path'].startswith('/{0}/'.format(self.engineio_path)):
            return self.engineio_asgi_app(scope)
        elif scope['type'] == 'http' and scope['path'] in self.static_files:
            return self.serve_static_file(scope)
        elif self.other_asgi_app is not None:
            return self.other_asgi_app(scope)
        elif scope['type'] == 'lifespan':
            return self.lifespan
        else:
            return self.not_found

    def engineio_asgi_app(self, scope):
        async def _app(receive, send):
            await self.engineio_server.handle_request(scope, receive, send)
        return _app

    def serve_static_file(self, scope):
        async def _send_static_file(receive, send):  # pragma: no cover
            event = await receive()
            if event['type'] == 'http.request':
                if scope['path'] in self.static_files:
                    content_type = self.static_files[scope['path']][
                        'content_type'].encode('utf-8')
                    filename = self.static_files[scope['path']]['filename']
                    status_code = 200
                    with open(filename, 'rb') as f:
                        payload = f.read()
                else:
                    content_type = b'text/plain'
                    status_code = 404
                    payload = b'not found'
                await send({'type': 'http.response.start',
                            'status': status_code,
                            'headers': [(b'Content-Type', content_type)]})
                await send({'type': 'http.response.body',
                            'body': payload})
        return _send_static_file

    async def lifespan(self, receive, send):
        event = await receive()
        if event['type'] == 'lifespan.startup':
            await send({'type': 'lifespan.startup.complete'})
        elif event['type'] == 'lifespan.shutdown':
            await send({'type': 'lifespan.shutdown.complete'})

    async def not_found(self, receive, send):
        """Return a 404 Not Found error to the client."""
        await send({'type': 'http.response.start',
                    'status': 404,
                    'headers': [(b'Content-Type', b'text/plain')]})
        await send({'type': 'http.response.body',
                    'body': b'not found'})


async def translate_request(scope, receive, send):
    class AwaitablePayload(object):  # pragma: no cover
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

    event = await receive()
    payload = b''
    if event['type'] == 'http.request':
        payload += event.get('body') or b''
        while event.get('more_body'):
            event = await receive()
            if event['type'] == 'http.request':
                payload += event.get('body') or b''
    elif event['type'] == 'websocket.connect':
        await send({'type': 'websocket.accept'})
    else:
        return {}

    raw_uri = scope['path'].encode('utf-8')
    if 'query_string' in scope and scope['query_string']:
        raw_uri += b'?' + scope['query_string']
    environ = {
        'wsgi.input': AwaitablePayload(payload),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.async': True,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'SERVER_SOFTWARE': 'asgi',
        'REQUEST_METHOD': scope.get('method', 'GET'),
        'PATH_INFO': scope['path'],
        'QUERY_STRING': scope.get('query_string', b'').decode('utf-8'),
        'RAW_URI': raw_uri.decode('utf-8'),
        'SCRIPT_NAME': '',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_PORT': '0',
        'SERVER_NAME': 'asgi',
        'SERVER_PORT': '0',
        'asgi.receive': receive,
        'asgi.send': send,
    }

    for hdr_name, hdr_value in scope['headers']:
        hdr_name = hdr_name.upper().decode('utf-8')
        hdr_value = hdr_value.decode('utf-8')
        if hdr_name == 'CONTENT-TYPE':
            environ['CONTENT_TYPE'] = hdr_value
            continue
        elif hdr_name == 'CONTENT-LENGTH':
            environ['CONTENT_LENGTH'] = hdr_value
            continue

        key = 'HTTP_%s' % hdr_name.replace('-', '_')
        if key in environ:
            hdr_value = '%s,%s' % (environ[key], hdr_value)

        environ[key] = hdr_value

    environ['wsgi.url_scheme'] = environ.get('HTTP_X_FORWARDED_PROTO', 'http')
    return environ


async def make_response(status, headers, payload, environ):
    headers = [(h[0].encode('utf-8'), h[1].encode('utf-8')) for h in headers]
    await environ['asgi.send']({'type': 'http.response.start',
                                'status': int(status.split(' ')[0]),
                                'headers': headers})
    await environ['asgi.send']({'type': 'http.response.body',
                                'body': payload})


class WebSocket(object):  # pragma: no cover
    """
    This wrapper class provides an asgi WebSocket interface that is
    somewhat compatible with eventlet's implementation.
    """
    def __init__(self, handler):
        self.handler = handler
        self.asgi_receive = None
        self.asgi_send = None

    async def __call__(self, environ):
        self.asgi_receive = environ['asgi.receive']
        self.asgi_send = environ['asgi.send']
        await self.handler(self)

    async def close(self):
        await self.asgi_send({'type': 'websocket.close'})

    async def send(self, message):
        msg_bytes = None
        msg_text = None
        if isinstance(message, bytes):
            msg_bytes = message
        else:
            msg_text = message
        await self.asgi_send({'type': 'websocket.send',
                              'bytes': msg_bytes,
                              'text': msg_text})

    async def wait(self):
        event = await self.asgi_receive()
        if event['type'] != 'websocket.receive':
            raise IOError()
        return event.get('bytes') or event.get('text')


_async = {
    'asyncio': True,
    'translate_request': translate_request,
    'make_response': make_response,
    'websocket': sys.modules[__name__],
    'websocket_class': 'WebSocket'
}
