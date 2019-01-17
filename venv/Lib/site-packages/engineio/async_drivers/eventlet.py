from __future__ import absolute_import

from eventlet.green.threading import Thread, Event
from eventlet.queue import Queue
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
    'thread': Thread,
    'queue': Queue,
    'event': Event,
    'websocket': WebSocketWSGI,
    'sleep': sleep,
}
