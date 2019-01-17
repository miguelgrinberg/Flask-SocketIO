import importlib
import sys

from eventlet import sleep
from eventlet.websocket import WebSocketWSGI as _WebSocketWSGI


class WebSocketWSGI(_WebSocketWSGI):
    def __init__(self, *args, **kwargs):
        super(WebSocketWSGI, self).__init__(*args, **kwargs)
        self._sock = None

    def __call__(self, environ, start_response):
        if 'eventlet.input' not in environ:
            raise RuntimeError('You need to use the eventlet server. '
                               'See the Deployment section of the '
                               'documentation for more information.')
        self._sock = environ['eventlet.input'].get_socket()
        return super(WebSocketWSGI, self).__call__(environ, start_response)


_async = {
    'threading': importlib.import_module('eventlet.green.threading'),
    'thread_class': 'Thread',
    'queue': importlib.import_module('eventlet.queue'),
    'queue_class': 'Queue',
    'websocket': sys.modules[__name__],
    'websocket_class': 'WebSocketWSGI',
    'sleep': sleep
}
