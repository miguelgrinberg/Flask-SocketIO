import logging
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from engineio.async_drivers import eventlet as async_eventlet


class TestAsyncEventlet(unittest.TestCase):
    def setUp(self):
        logging.getLogger('engineio').setLevel(logging.NOTSET)

    def test_bad_environ(self):
        wsgi = async_eventlet.WebSocketWSGI(None)
        environ = {'foo': 'bar'}
        start_response = 'bar'
        self.assertRaises(RuntimeError, wsgi, environ, start_response)

    @mock.patch('engineio.async_drivers.eventlet._WebSocketWSGI.__call__',
                return_value='data')
    def test_wsgi_call(self, _WebSocketWSGI):
        _WebSocketWSGI.__call__ = lambda e, s: 'data'
        environ = {'eventlet.input': mock.MagicMock()}
        start_response = 'bar'
        wsgi = async_eventlet.WebSocketWSGI(None)
        self.assertEqual(wsgi(environ, start_response), 'data')
