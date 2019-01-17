import gzip
import importlib
import json
import logging
import sys
import time
import unittest
import zlib

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from engineio import exceptions
from engineio import packet
from engineio import payload
from engineio import server


original_import_module = importlib.import_module


def _mock_import(module, *args, **kwargs):
    if module.startswith('engineio.'):
        return original_import_module(module, *args, **kwargs)
    return module


class TestServer(unittest.TestCase):
    _mock_async = mock.MagicMock()
    _mock_async._async = {
        'threading': 't',
        'thread_class': 'tc',
        'queue': 'q',
        'queue_class': 'qc',
        'websocket': 'w',
        'websocket_class': 'wc'
    }

    def _get_mock_socket(self):
        mock_socket = mock.MagicMock()
        mock_socket.closed = False
        mock_socket.closing = False
        mock_socket.upgraded = False
        return mock_socket

    @classmethod
    def setUpClass(cls):
        server.Server._default_monitor_clients = False

    @classmethod
    def tearDownClass(cls):
        server.Server._default_monitor_clients = True

    def setUp(self):
        logging.getLogger('engineio').setLevel(logging.NOTSET)

    def tearDown(self):
        # restore JSON encoder, in case a test changed it
        packet.Packet.json = json

    def test_is_asyncio_based(self):
        s = server.Server()
        self.assertEqual(s.is_asyncio_based(), False)

    def test_async_modes(self):
        s = server.Server()
        self.assertEqual(s.async_modes(), ['eventlet', 'gevent_uwsgi',
                                           'gevent', 'threading'])

    def test_create(self):
        kwargs = {
            'ping_timeout': 1,
            'ping_interval': 2,
            'max_http_buffer_size': 3,
            'allow_upgrades': False,
            'http_compression': False,
            'compression_threshold': 4,
            'cookie': 'foo',
            'cors_allowed_origins': ['foo', 'bar', 'baz'],
            'cors_credentials': False,
            'async_handlers': False}
        s = server.Server(**kwargs)
        for arg in six.iterkeys(kwargs):
            self.assertEqual(getattr(s, arg), kwargs[arg])

    def test_create_ignores_kwargs(self):
        server.Server(foo='bar')  # this should not raise

    def test_async_mode_threading(self):
        s = server.Server(async_mode='threading')
        self.assertEqual(s.async_mode, 'threading')

        import threading
        try:
            import queue
        except ImportError:
            import Queue as queue

        self.assertEqual(s._async['threading'], threading)
        self.assertEqual(s._async['thread_class'], 'Thread')
        self.assertEqual(s._async['queue'], queue)
        self.assertEqual(s._async['queue_class'], 'Queue')
        self.assertEqual(s._async['websocket'], None)
        self.assertEqual(s._async['websocket_class'], None)

    def test_async_mode_eventlet(self):
        s = server.Server(async_mode='eventlet')
        self.assertEqual(s.async_mode, 'eventlet')

        from eventlet.green import threading
        from eventlet import queue
        from engineio.async_drivers import eventlet as async_eventlet

        self.assertEqual(s._async['threading'], threading)
        self.assertEqual(s._async['thread_class'], 'Thread')
        self.assertEqual(s._async['queue'], queue)
        self.assertEqual(s._async['queue_class'], 'Queue')
        self.assertEqual(s._async['websocket'], async_eventlet)
        self.assertEqual(s._async['websocket_class'], 'WebSocketWSGI')

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent_uwsgi(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['uwsgi'] = mock.MagicMock()
        s = server.Server(async_mode='gevent_uwsgi')
        self.assertEqual(s.async_mode, 'gevent_uwsgi')

        from engineio.async_drivers import gevent_uwsgi as async_gevent_uwsgi

        self.assertEqual(s._async['threading'], async_gevent_uwsgi)
        self.assertEqual(s._async['thread_class'], 'Thread')
        self.assertEqual(s._async['queue'], 'gevent.queue')
        self.assertEqual(s._async['queue_class'], 'JoinableQueue')
        self.assertEqual(s._async['websocket'], async_gevent_uwsgi)
        self.assertEqual(s._async['websocket_class'], 'uWSGIWebSocket')
        del sys.modules['gevent']
        del sys.modules['uwsgi']
        del sys.modules['engineio.async_drivers.gevent_uwsgi']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent_uwsgi_without_uwsgi(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['uwsgi'] = None
        self.assertRaises(ValueError, server.Server,
                          async_mode='gevent_uwsgi')
        del sys.modules['gevent']
        del sys.modules['uwsgi']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent_uwsgi_without_websocket(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['uwsgi'] = mock.MagicMock()
        del sys.modules['uwsgi'].websocket_handshake
        s = server.Server(async_mode='gevent_uwsgi')
        self.assertEqual(s.async_mode, 'gevent_uwsgi')

        from engineio.async_drivers import gevent_uwsgi as async_gevent_uwsgi

        self.assertEqual(s._async['threading'], async_gevent_uwsgi)
        self.assertEqual(s._async['thread_class'], 'Thread')
        self.assertEqual(s._async['queue'], 'gevent.queue')
        self.assertEqual(s._async['queue_class'], 'JoinableQueue')
        self.assertEqual(s._async['websocket'], None)
        self.assertEqual(s._async['websocket_class'], None)
        del sys.modules['gevent']
        del sys.modules['uwsgi']
        del sys.modules['engineio.async_drivers.gevent_uwsgi']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['geventwebsocket'] = 'geventwebsocket'
        s = server.Server(async_mode='gevent')
        self.assertEqual(s.async_mode, 'gevent')

        from engineio.async_drivers import gevent as async_gevent

        self.assertEqual(s._async['threading'], async_gevent)
        self.assertEqual(s._async['thread_class'], 'Thread')
        self.assertEqual(s._async['queue'], 'gevent.queue')
        self.assertEqual(s._async['queue_class'], 'JoinableQueue')
        self.assertEqual(s._async['websocket'], async_gevent)
        self.assertEqual(s._async['websocket_class'], 'WebSocketWSGI')
        del sys.modules['gevent']
        del sys.modules['geventwebsocket']
        del sys.modules['engineio.async_drivers.gevent']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent_without_websocket(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['geventwebsocket'] = None
        s = server.Server(async_mode='gevent')
        self.assertEqual(s.async_mode, 'gevent')

        from engineio.async_drivers import gevent as async_gevent

        self.assertEqual(s._async['threading'], async_gevent)
        self.assertEqual(s._async['thread_class'], 'Thread')
        self.assertEqual(s._async['queue'], 'gevent.queue')
        self.assertEqual(s._async['queue_class'], 'JoinableQueue')
        self.assertEqual(s._async['websocket'], None)
        self.assertEqual(s._async['websocket_class'], None)
        del sys.modules['gevent']
        del sys.modules['geventwebsocket']
        del sys.modules['engineio.async_drivers.gevent']

    @unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_aiohttp(self, import_module):
        sys.modules['aiohttp'] = mock.MagicMock()
        self.assertRaises(ValueError, server.Server, async_mode='aiohttp')

    @mock.patch('importlib.import_module', side_effect=[ImportError])
    def test_async_mode_invalid(self, import_module):
        self.assertRaises(ValueError, server.Server, async_mode='foo')

    @mock.patch('importlib.import_module', side_effect=[_mock_async])
    def test_async_mode_auto_eventlet(self, import_module):
        s = server.Server()
        self.assertEqual(s.async_mode, 'eventlet')

    @mock.patch('importlib.import_module', side_effect=[ImportError,
                                                        _mock_async])
    def test_async_mode_auto_gevent_uwsgi(self, import_module):
        s = server.Server()
        self.assertEqual(s.async_mode, 'gevent_uwsgi')

    @mock.patch('importlib.import_module', side_effect=[ImportError,
                                                        ImportError,
                                                        _mock_async])
    def test_async_mode_auto_gevent(self, import_module):
        s = server.Server()
        self.assertEqual(s.async_mode, 'gevent')

    @mock.patch('importlib.import_module', side_effect=[ImportError,
                                                        ImportError,
                                                        ImportError,
                                                        _mock_async])
    def test_async_mode_auto_threading(self, import_module):
        s = server.Server()
        self.assertEqual(s.async_mode, 'threading')

    def test_generate_id(self):
        s = server.Server()
        self.assertNotEqual(s._generate_id(), s._generate_id())

    def test_on_event(self):
        s = server.Server()

        @s.on('connect')
        def foo():
            pass
        s.on('disconnect', foo)

        self.assertEqual(s.handlers['connect'], foo)
        self.assertEqual(s.handlers['disconnect'], foo)

    def test_on_event_invalid(self):
        s = server.Server()
        self.assertRaises(ValueError, s.on, 'invalid')

    def test_trigger_event(self):
        s = server.Server()
        f = {}

        @s.on('connect')
        def foo(sid, environ):
            return sid + environ

        @s.on('message')
        def bar(sid, data):
            f['bar'] = sid + data
            return 'bar'

        r = s._trigger_event('connect', 1, 2, run_async=False)
        self.assertEqual(r, 3)
        r = s._trigger_event('message', 3, 4, run_async=True)
        r.join()
        self.assertEqual(f['bar'], 7)
        r = s._trigger_event('message', 5, 6)
        self.assertEqual(r, 'bar')

    def test_trigger_event_error(self):
        s = server.Server()

        @s.on('connect')
        def foo(sid, environ):
            return 1 / 0

        @s.on('message')
        def bar(sid, data):
            return 1 / 0

        r = s._trigger_event('connect', 1, 2, run_async=False)
        self.assertEqual(r, False)
        r = s._trigger_event('message', 3, 4, run_async=False)
        self.assertEqual(r, None)

    def test_close_one_socket(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        s.sockets['foo'] = mock_socket
        s.disconnect('foo')
        self.assertEqual(mock_socket.close.call_count, 1)
        self.assertNotIn('foo', s.sockets)

    def test_close_all_sockets(self):
        s = server.Server()
        mock_sockets = {}
        for sid in ['foo', 'bar', 'baz']:
            mock_sockets[sid] = self._get_mock_socket()
            s.sockets[sid] = mock_sockets[sid]
        s.disconnect()
        for socket in six.itervalues(mock_sockets):
            self.assertEqual(socket.close.call_count, 1)
        self.assertEqual(s.sockets, {})

    def test_upgrades(self):
        s = server.Server()
        s.sockets['foo'] = self._get_mock_socket()
        self.assertEqual(s._upgrades('foo', 'polling'), ['websocket'])
        self.assertEqual(s._upgrades('foo', 'websocket'), [])
        s.sockets['foo'].upgraded = True
        self.assertEqual(s._upgrades('foo', 'polling'), [])
        self.assertEqual(s._upgrades('foo', 'websocket'), [])
        s.allow_upgrades = False
        s.sockets['foo'].upgraded = True
        self.assertEqual(s._upgrades('foo', 'polling'), [])
        self.assertEqual(s._upgrades('foo', 'websocket'), [])

    def test_transport(self):
        s = server.Server()
        s.sockets['foo'] = self._get_mock_socket()
        s.sockets['foo'].upgraded = False
        s.sockets['bar'] = self._get_mock_socket()
        s.sockets['bar'].upgraded = True
        self.assertEqual(s.transport('foo'), 'polling')
        self.assertEqual(s.transport('bar'), 'websocket')

    def test_bad_session(self):
        s = server.Server()
        s.sockets['foo'] = 'client'
        self.assertRaises(KeyError, s._get_socket, 'bar')

    def test_closed_socket(self):
        s = server.Server()
        s.sockets['foo'] = self._get_mock_socket()
        s.sockets['foo'].closed = True
        self.assertRaises(KeyError, s._get_socket, 'foo')

    def test_jsonp_not_supported(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'j=abc'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    def test_connect(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertEqual(len(s.sockets), 1)
        self.assertEqual(start_response.call_count, 1)
        self.assertEqual(start_response.call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'application/octet-stream'),
                      start_response.call_args[0][1])
        self.assertEqual(len(r), 1)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].packet_type, packet.OPEN)
        self.assertIn('upgrades', packets[0].data)
        self.assertEqual(packets[0].data['upgrades'], ['websocket'])
        self.assertIn('sid', packets[0].data)

    def test_connect_no_upgrades(self):
        s = server.Server(allow_upgrades=False)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(packets[0].data['upgrades'], [])

    def test_connect_b64_with_1(self):
        s = server.Server(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'b64=1'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertTrue(start_response.call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'text/plain; charset=UTF-8'),
                      start_response.call_args[0][1])
        s.send('1', b'\x00\x01\x02', binary=True)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=1'}
        r = s.handle_request(environ, start_response)
        self.assertEqual(r[0], b'6:b4AAEC')

    def test_connect_b64_with_true(self):
        s = server.Server(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'b64=true'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertTrue(start_response.call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'text/plain; charset=UTF-8'),
                      start_response.call_args[0][1])
        s.send('1', b'\x00\x01\x02', binary=True)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=true'}
        r = s.handle_request(environ, start_response)
        self.assertEqual(r[0], b'6:b4AAEC')

    def test_connect_b64_with_0(self):
        s = server.Server(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'b64=0'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertTrue(start_response.call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'application/octet-stream'),
                      start_response.call_args[0][1])
        s.send('1', b'\x00\x01\x02', binary=True)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=0'}
        r = s.handle_request(environ, start_response)
        self.assertEqual(r[0], b'\x01\x04\xff\x04\x00\x01\x02')

    def test_connect_b64_with_false(self):
        s = server.Server(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'b64=false'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertTrue(start_response.call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'application/octet-stream'),
                      start_response.call_args[0][1])
        s.send('1', b'\x00\x01\x02', binary=True)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=false'}
        r = s.handle_request(environ, start_response)
        self.assertEqual(r[0], b'\x01\x04\xff\x04\x00\x01\x02')

    def test_connect_custom_ping_times(self):
        s = server.Server(ping_timeout=123, ping_interval=456)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(packets[0].data['pingTimeout'], 123000)
        self.assertEqual(packets[0].data['pingInterval'], 456000)

    @mock.patch('engineio.socket.Socket.poll',
                side_effect=exceptions.QueueEmpty)
    def test_connect_bad_poll(self, poll):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    @mock.patch('engineio.socket.Socket',
                return_value=mock.MagicMock(connected=False, closed=False))
    def test_connect_transport_websocket(self, Socket):
        s = server.Server()
        s._generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET',
                   'QUERY_STRING': 'transport=websocket'}
        start_response = mock.MagicMock()
        # force socket to stay open, so that we can check it later
        Socket().closed = False
        s.handle_request(environ, start_response)
        self.assertEqual(s.sockets['123'].send.call_args[0][0].packet_type,
                         packet.OPEN)

    @mock.patch('engineio.socket.Socket',
                return_value=mock.MagicMock(connected=False, closed=False))
    def test_connect_transport_websocket_closed(self, Socket):
        s = server.Server()
        s._generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET',
                   'QUERY_STRING': 'transport=websocket'}
        start_response = mock.MagicMock()

        def mock_handle(environ, start_response):
            s.sockets['123'].closed = True

        Socket().handle_get_request = mock_handle
        s.handle_request(environ, start_response)
        self.assertNotIn('123', s.sockets)

    def test_connect_transport_invalid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'transport=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    def test_connect_cors_headers(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', '*'), headers)
        self.assertIn(('Access-Control-Allow-Credentials', 'true'), headers)

    def test_connect_cors_allowed_origin(self):
        s = server.Server(cors_allowed_origins=['a', 'b'])
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '',
                   'HTTP_ORIGIN': 'b'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', 'b'), headers)

    def test_connect_cors_not_allowed_origin(self):
        s = server.Server(cors_allowed_origins=['a', 'b'])
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '',
                   'HTTP_ORIGIN': 'c'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertNotIn(('Access-Control-Allow-Origin', 'c'), headers)
        self.assertNotIn(('Access-Control-Allow-Origin', '*'), headers)

    def test_connect_cors_headers_all_origins(self):
        s = server.Server(cors_allowed_origins='*')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', '*'), headers)
        self.assertIn(('Access-Control-Allow-Credentials', 'true'), headers)

    def test_connect_cors_headers_one_origin(self):
        s = server.Server(cors_allowed_origins='a')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '',
                   'HTTP_ORIGIN': 'a'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', 'a'), headers)
        self.assertIn(('Access-Control-Allow-Credentials', 'true'), headers)

    def test_connect_cors_headers_one_origin_not_allowed(self):
        s = server.Server(cors_allowed_origins='a')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '',
                   'HTTP_ORIGIN': 'b'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertNotIn(('Access-Control-Allow-Origin', 'b'), headers)
        self.assertNotIn(('Access-Control-Allow-Origin', '*'), headers)

    def test_connect_cors_no_credentials(self):
        s = server.Server(cors_credentials=False)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertNotIn(('Access-Control-Allow-Credentials', 'true'), headers)

    def test_cors_options(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'OPTIONS', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Methods', 'OPTIONS, GET, POST'),
                      headers)

    def test_cors_request_headers(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET',
                   'HTTP_ACCESS_CONTROL_REQUEST_HEADERS': 'Foo, Bar'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Headers', 'Foo, Bar'), headers)

    def test_connect_event(self):
        s = server.Server()
        s._generate_id = mock.MagicMock(return_value='123')
        mock_event = mock.MagicMock()
        s.on('connect')(mock_event)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        mock_event.assert_called_once_with('123', environ)
        self.assertEqual(len(s.sockets), 1)

    def test_connect_event_rejects(self):
        s = server.Server()
        s._generate_id = mock.MagicMock(return_value='123')
        mock_event = mock.MagicMock(return_value=False)
        s.on('connect')(mock_event)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(len(s.sockets), 0)
        self.assertEqual(start_response.call_args[0][0], '401 UNAUTHORIZED')

    def test_method_not_found(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'PUT', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '405 METHOD NOT FOUND')

    def test_get_request_with_bad_sid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    def test_post_request_with_bad_sid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    def test_send(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        s.sockets['foo'] = mock_socket
        s.send('foo', 'hello')
        self.assertEqual(mock_socket.send.call_count, 1)
        self.assertEqual(mock_socket.send.call_args[0][0].packet_type,
                         packet.MESSAGE)
        self.assertEqual(mock_socket.send.call_args[0][0].data, 'hello')

    def test_send_unknown_socket(self):
        s = server.Server()
        # just ensure no exceptions are raised
        s.send('foo', 'hello')

    def test_get_request(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '200 OK')
        self.assertEqual(len(r), 1)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].packet_type, packet.MESSAGE)

    def test_get_request_custom_response(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(side_effect=['resp'])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        self.assertEqual(s.handle_request(environ, start_response), 'resp')

    def test_get_request_closes_socket(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()

        def mock_get_request(*args, **kwargs):
            mock_socket.closed = True
            return 'resp'

        mock_socket.handle_get_request = mock_get_request
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        self.assertEqual(s.handle_request(environ, start_response), 'resp')
        self.assertNotIn('foo', s.sockets)

    def test_get_request_error(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            side_effect=[exceptions.QueueEmpty])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')
        self.assertEqual(len(s.sockets), 0)

    def test_post_request(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_post_request = mock.MagicMock()
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '200 OK')

    def test_post_request_error(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_post_request = mock.MagicMock(
            side_effect=[exceptions.EngineIOError])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')
        self.assertNotIn('foo', s.sockets)

    @staticmethod
    def _gzip_decompress(b):
        bytesio = six.BytesIO(b)
        with gzip.GzipFile(fileobj=bytesio, mode='r') as gz:
            return gz.read()

    def test_gzip_compression(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'HTTP_ACCEPT_ENCODING': 'gzip,deflate'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertIn(('Content-Encoding', 'gzip'),
                      start_response.call_args[0][1])
        self._gzip_decompress(r[0])

    def test_deflate_compression(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'HTTP_ACCEPT_ENCODING': 'deflate;q=1,gzip'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertIn(('Content-Encoding', 'deflate'),
                      start_response.call_args[0][1])
        zlib.decompress(r[0])

    def test_gzip_compression_threshold(self):
        s = server.Server(compression_threshold=1000)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'HTTP_ACCEPT_ENCODING': 'gzip'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_compression_disabled(self):
        s = server.Server(http_compression=False, compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'HTTP_ACCEPT_ENCODING': 'gzip'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_compression_unknown(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'HTTP_ACCEPT_ENCODING': 'rar'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_compression_no_encoding(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'HTTP_ACCEPT_ENCODING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_cookie(self):
        s = server.Server(cookie='sid')
        s._generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertIn(('Set-Cookie', 'sid=123'),
                      start_response.call_args[0][1])

    def test_no_cookie(self):
        s = server.Server(cookie=None)
        s._generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Set-Cookie')

    def test_logger(self):
        s = server.Server(logger=False)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.ERROR)
        s.logger.setLevel(logging.NOTSET)
        s = server.Server(logger=True)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.INFO)
        s.logger.setLevel(logging.WARNING)
        s = server.Server(logger=True)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.WARNING)
        s.logger.setLevel(logging.NOTSET)
        my_logger = logging.Logger('foo')
        s = server.Server(logger=my_logger)
        self.assertEqual(s.logger, my_logger)

    def test_custom_json(self):
        # Warning: this test cannot run in parallel with other tests, as it
        # changes the JSON encoding/decoding functions

        class CustomJSON(object):
            @staticmethod
            def dumps(*args, **kwargs):
                return '*** encoded ***'

            @staticmethod
            def loads(*args, **kwargs):
                return '+++ decoded +++'

        server.Server(json=CustomJSON)
        pkt = packet.Packet(packet.MESSAGE, data={'foo': 'bar'})
        self.assertEqual(pkt.encode(), b'4*** encoded ***')
        pkt2 = packet.Packet(encoded_packet=pkt.encode())
        self.assertEqual(pkt2.data, '+++ decoded +++')

        # restore the default JSON module
        packet.Packet.json = json

    def test_background_tasks(self):
        flag = {}

        def bg_task():
            flag['task'] = True

        s = server.Server()
        task = s.start_background_task(bg_task)
        task.join()
        self.assertIn('task', flag)
        self.assertTrue(flag['task'])

    def test_sleep(self):
        s = server.Server()
        t = time.time()
        s.sleep(0.1)
        self.assertTrue(time.time() - t > 0.1)

    def test_service_task_started(self):
        s = server.Server(monitor_clients=True)
        s._service_task = mock.MagicMock()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        s._service_task.assert_called_once_with()
