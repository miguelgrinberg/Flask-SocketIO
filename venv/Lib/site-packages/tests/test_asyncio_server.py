import gzip
import json
import logging
import sys
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
if sys.version_info >= (3, 5):
    import asyncio
    from asyncio import coroutine
    from engineio import asyncio_server
    from engineio.async_drivers import aiohttp as async_aiohttp
else:
    # mock coroutine so that Python 2 doesn't complain
    def coroutine(f):
        return f


def AsyncMock(*args, **kwargs):
    """Return a mock asynchronous function."""
    m = mock.MagicMock(*args, **kwargs)

    @coroutine
    def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class TestAsyncServer(unittest.TestCase):
    @staticmethod
    def get_async_mock(environ={'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}):
        a = mock.MagicMock()
        a._async = {
            'asyncio': True,
            'create_route': mock.MagicMock(),
            'translate_request': mock.MagicMock(),
            'make_response': mock.MagicMock(),
            'websocket': 'w',
            'websocket_class': 'wc'
        }
        a._async['translate_request'].return_value = environ
        a._async['make_response'].return_value = 'response'
        return a

    def _get_mock_socket(self):
        mock_socket = mock.MagicMock()
        mock_socket.connected = False
        mock_socket.closed = False
        mock_socket.closing = False
        mock_socket.upgraded = False
        mock_socket.send = AsyncMock()
        mock_socket.handle_get_request = AsyncMock()
        mock_socket.handle_post_request = AsyncMock()
        mock_socket.check_ping_timeout = AsyncMock()
        mock_socket.close = AsyncMock()
        return mock_socket

    @classmethod
    def setUpClass(cls):
        asyncio_server.AsyncServer._default_monitor_clients = False

    @classmethod
    def tearDownClass(cls):
        asyncio_server.AsyncServer._default_monitor_clients = True

    def setUp(self):
        logging.getLogger('engineio').setLevel(logging.NOTSET)

    def tearDown(self):
        # restore JSON encoder, in case a test changed it
        packet.Packet.json = json

    def test_is_asyncio_based(self):
        s = asyncio_server.AsyncServer()
        self.assertEqual(s.is_asyncio_based(), True)

    def test_async_modes(self):
        s = asyncio_server.AsyncServer()
        self.assertEqual(s.async_modes(), ['aiohttp', 'sanic', 'tornado',
                                           'asgi'])

    def test_async_mode_aiohttp(self):
        s = asyncio_server.AsyncServer(async_mode='aiohttp')
        self.assertEqual(s.async_mode, 'aiohttp')
        self.assertEqual(s._async['asyncio'], True)
        self.assertEqual(s._async['create_route'], async_aiohttp.create_route)
        self.assertEqual(s._async['translate_request'],
                         async_aiohttp.translate_request)
        self.assertEqual(s._async['make_response'],
                         async_aiohttp.make_response)
        self.assertEqual(s._async['websocket'], async_aiohttp)
        self.assertEqual(s._async['websocket_class'], 'WebSocket')

    @mock.patch('importlib.import_module')
    def test_async_mode_auto_aiohttp(self, import_module):
        import_module.side_effect = [self.get_async_mock()]
        s = asyncio_server.AsyncServer()
        self.assertEqual(s.async_mode, 'aiohttp')

    def test_async_modes_wsgi(self):
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='eventlet')
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='gevent')
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='gevent_uwsgi')
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='threading')

    @mock.patch('importlib.import_module')
    def test_attach(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.attach('app', engineio_path='abc')
        a._async['create_route'].assert_called_with('app', s, '/abc/')
        s.attach('app', engineio_path='/def/')
        a._async['create_route'].assert_called_with('app', s, '/def/')
        s.attach('app', engineio_path='/ghi')
        a._async['create_route'].assert_called_with('app', s, '/ghi/')
        s.attach('app', engineio_path='jkl/')
        a._async['create_route'].assert_called_with('app', s, '/jkl/')

    def test_disconnect(self):
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        _run(s.disconnect('foo'))
        self.assertEqual(mock_socket.close.mock.call_count, 1)
        mock_socket.close.mock.assert_called_once_with()
        self.assertNotIn('foo', s.sockets)

    def test_disconnect_all(self):
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_foo = self._get_mock_socket()
        s.sockets['bar'] = mock_bar = self._get_mock_socket()
        _run(s.disconnect())
        self.assertEqual(mock_foo.close.mock.call_count, 1)
        self.assertEqual(mock_bar.close.mock.call_count, 1)
        mock_foo.close.mock.assert_called_once_with()
        mock_bar.close.mock.assert_called_once_with()
        self.assertNotIn('foo', s.sockets)
        self.assertNotIn('bar', s.sockets)

    @mock.patch('importlib.import_module')
    def test_jsonp_not_supported(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'j=abc'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        response = _run(s.handle_request('request'))
        self.assertEqual(response, 'response')
        a._async['translate_request'].assert_called_once_with('request')
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '400 BAD REQUEST')

    @mock.patch('importlib.import_module')
    def test_connect(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        self.assertEqual(len(s.sockets), 1)
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'application/octet-stream'),
                      a._async['make_response'].call_args[0][1])
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2]).packets
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].packet_type, packet.OPEN)
        self.assertIn('upgrades', packets[0].data)
        self.assertEqual(packets[0].data['upgrades'], ['websocket'])
        self.assertIn('sid', packets[0].data)

    @mock.patch('importlib.import_module')
    def test_connect_async_request_response_handlers(self, import_module):
        a = self.get_async_mock()
        a._async['translate_request'] = AsyncMock(
            return_value=a._async['translate_request'].return_value)
        a._async['make_response'] = AsyncMock(
            return_value=a._async['make_response'].return_value)
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        self.assertEqual(len(s.sockets), 1)
        self.assertEqual(a._async['make_response'].mock.call_count, 1)
        self.assertEqual(a._async['make_response'].mock.call_args[0][0],
                         '200 OK')
        self.assertIn(('Content-Type', 'application/octet-stream'),
                      a._async['make_response'].mock.call_args[0][1])
        packets = payload.Payload(encoded_payload=a._async[
            'make_response'].mock.call_args[0][2]).packets
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].packet_type, packet.OPEN)
        self.assertIn('upgrades', packets[0].data)
        self.assertEqual(packets[0].data['upgrades'], ['websocket'])
        self.assertIn('sid', packets[0].data)

    @mock.patch('importlib.import_module')
    def test_connect_no_upgrades(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(allow_upgrades=False)
        _run(s.handle_request('request'))
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2]).packets
        self.assertEqual(packets[0].data['upgrades'], [])

    @mock.patch('importlib.import_module')
    def test_connect_b64_with_1(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'b64=1'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'text/plain; charset=UTF-8'),
                      a._async['make_response'].call_args[0][1])
        _run(s.send('1', b'\x00\x01\x02', binary=True))
        a._async['translate_request'].return_value = {
            'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=1'}
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][2],
                         b'6:b4AAEC')

    @mock.patch('importlib.import_module')
    def test_connect_b64_with_true(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'b64=true'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'text/plain; charset=UTF-8'),
                      a._async['make_response'].call_args[0][1])
        _run(s.send('1', b'\x00\x01\x02', binary=True))
        a._async['translate_request'].return_value = {
            'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=true'}
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][2],
                         b'6:b4AAEC')

    @mock.patch('importlib.import_module')
    def test_connect_b64_with_0(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'b64=0'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'application/octet-stream'),
                      a._async['make_response'].call_args[0][1])
        _run(s.send('1', b'\x00\x01\x02', binary=True))
        a._async['translate_request'].return_value = {
            'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=0'}
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][2],
                         b'\x01\x04\xff\x04\x00\x01\x02')

    @mock.patch('importlib.import_module')
    def test_connect_b64_with_false(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'b64=false'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(allow_upgrades=False)
        s._generate_id = mock.MagicMock(return_value='1')
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0], '200 OK')
        self.assertIn(('Content-Type', 'application/octet-stream'),
                      a._async['make_response'].call_args[0][1])
        _run(s.send('1', b'\x00\x01\x02', binary=True))
        a._async['translate_request'].return_value = {
            'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=1&b64=false'}
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][2],
                         b'\x01\x04\xff\x04\x00\x01\x02')

    @mock.patch('importlib.import_module')
    def test_connect_custom_ping_times(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(ping_timeout=123, ping_interval=456)
        _run(s.handle_request('request'))
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2]).packets
        self.assertEqual(packets[0].data['pingTimeout'], 123000)
        self.assertEqual(packets[0].data['pingInterval'], 456000)

    @mock.patch('engineio.asyncio_socket.AsyncSocket')
    @mock.patch('importlib.import_module')
    def test_connect_bad_poll(self, import_module, AsyncSocket):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        AsyncSocket.return_value = self._get_mock_socket()
        AsyncSocket.return_value.poll.side_effect = [exceptions.QueueEmpty]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '400 BAD REQUEST')

    @mock.patch('engineio.asyncio_socket.AsyncSocket')
    @mock.patch('importlib.import_module')
    def test_connect_transport_websocket(self, import_module, AsyncSocket):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'transport=websocket'})
        import_module.side_effect = [a]
        AsyncSocket.return_value = self._get_mock_socket()
        s = asyncio_server.AsyncServer()
        s._generate_id = mock.MagicMock(return_value='123')
        # force socket to stay open, so that we can check it later
        AsyncSocket().closed = False
        _run(s.handle_request('request'))
        self.assertEqual(
            s.sockets['123'].send.mock.call_args[0][0].packet_type,
            packet.OPEN)

    @mock.patch('engineio.asyncio_socket.AsyncSocket')
    @mock.patch('importlib.import_module')
    def test_connect_transport_websocket_closed(self, import_module,
                                                AsyncSocket):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'transport=websocket'})
        import_module.side_effect = [a]
        AsyncSocket.return_value = self._get_mock_socket()
        s = asyncio_server.AsyncServer()
        s._generate_id = mock.MagicMock(return_value='123')

        # this mock handler just closes the socket, as it would happen on a
        # real websocket exchange
        @coroutine
        def mock_handle(environ):
            s.sockets['123'].closed = True

        AsyncSocket().handle_get_request = mock_handle
        _run(s.handle_request('request'))
        self.assertNotIn('123', s.sockets)  # socket should close on its own

    @mock.patch('importlib.import_module')
    def test_connect_transport_invalid(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'transport=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_count, 1)
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '400 BAD REQUEST')

    @mock.patch('importlib.import_module')
    def test_connect_cors_headers(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', '*'), headers)
        self.assertIn(('Access-Control-Allow-Credentials', 'true'), headers)

    @mock.patch('importlib.import_module')
    def test_connect_cors_allowed_origin(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET', 'QUERY_STRING': '',
                                 'HTTP_ORIGIN': 'b'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(cors_allowed_origins=['a', 'b'])
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', 'b'), headers)

    @mock.patch('importlib.import_module')
    def test_connect_cors_not_allowed_origin(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET', 'QUERY_STRING': '',
                                 'HTTP_ORIGIN': 'c'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(cors_allowed_origins=['a', 'b'])
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertNotIn(('Access-Control-Allow-Origin', 'c'), headers)
        self.assertNotIn(('Access-Control-Allow-Origin', '*'), headers)

    @mock.patch('importlib.import_module')
    def test_connect_cors_no_credentials(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(cors_credentials=False)
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertNotIn(('Access-Control-Allow-Credentials', 'true'), headers)

    @mock.patch('importlib.import_module')
    def test_connect_cors_options(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'OPTIONS',
                                 'QUERY_STRING': ''})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(cors_credentials=False)
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertIn(('Access-Control-Allow-Methods',
                       'OPTIONS, GET, POST'), headers)

    @mock.patch('importlib.import_module')
    def test_connect_event(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s._generate_id = mock.MagicMock(return_value='123')

        def mock_connect(sid, environ):
            return True

        s.on('connect', handler=mock_connect)
        _run(s.handle_request('request'))
        self.assertEqual(len(s.sockets), 1)

    @mock.patch('importlib.import_module')
    def test_connect_event_rejects(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s._generate_id = mock.MagicMock(return_value='123')

        def mock_connect(sid, environ):
            return False

        s.on('connect')(mock_connect)
        _run(s.handle_request('request'))
        self.assertEqual(len(s.sockets), 0)
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '401 UNAUTHORIZED')

    @mock.patch('importlib.import_module')
    def test_method_not_found(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'PUT', 'QUERY_STRING': ''})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        self.assertEqual(len(s.sockets), 0)
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '405 METHOD NOT FOUND')

    @mock.patch('importlib.import_module')
    def test_get_request_with_bad_sid(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        self.assertEqual(len(s.sockets), 0)
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '400 BAD REQUEST')

    @mock.patch('importlib.import_module')
    def test_post_request_with_bad_sid(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'POST',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        _run(s.handle_request('request'))
        self.assertEqual(len(s.sockets), 0)
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '400 BAD REQUEST')

    @mock.patch('importlib.import_module')
    def test_send(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        _run(s.send('foo', 'hello'))
        self.assertEqual(mock_socket.send.mock.call_count, 1)
        self.assertEqual(mock_socket.send.mock.call_args[0][0].packet_type,
                         packet.MESSAGE)
        self.assertEqual(mock_socket.send.mock.call_args[0][0].data, 'hello')

    @mock.patch('importlib.import_module')
    def test_send_unknown_socket(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        # just ensure no exceptions are raised
        _run(s.send('foo', 'hello'))

    @mock.patch('importlib.import_module')
    def test_get_request(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = \
            [packet.Packet(packet.MESSAGE, data='hello')]
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][0], '200 OK')
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2]).packets
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].packet_type, packet.MESSAGE)

    @mock.patch('importlib.import_module')
    def test_get_request_custom_response(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = 'resp'
        r = _run(s.handle_request('request'))
        self.assertEqual(r, 'resp')

    @mock.patch('importlib.import_module')
    def test_get_request_closes_socket(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()

        @coroutine
        def mock_get_request(*args, **kwargs):
            mock_socket.closed = True
            return 'resp'

        mock_socket.handle_get_request.mock.return_value = mock_get_request()
        r = _run(s.handle_request('request'))
        self.assertEqual(r, 'resp')
        self.assertNotIn('foo', s.sockets)

    @mock.patch('importlib.import_module')
    def test_get_request_error(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()

        @coroutine
        def mock_get_request(*args, **kwargs):
            raise exceptions.QueueEmpty()

        mock_socket.handle_get_request.mock.return_value = mock_get_request()
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '400 BAD REQUEST')
        self.assertEqual(len(s.sockets), 0)

    @mock.patch('importlib.import_module')
    def test_post_request(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'POST',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = self._get_mock_socket()
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][0], '200 OK')

    @mock.patch('importlib.import_module')
    def test_post_request_error(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'POST',
                                 'QUERY_STRING': 'sid=foo'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()

        @coroutine
        def mock_post_request(*args, **kwargs):
            raise exceptions.ContentTooLongError()

        mock_socket.handle_post_request.mock.return_value = mock_post_request()
        _run(s.handle_request('request'))
        self.assertEqual(a._async['make_response'].call_args[0][0],
                         '400 BAD REQUEST')

    @staticmethod
    def _gzip_decompress(b):
        bytesio = six.BytesIO(b)
        with gzip.GzipFile(fileobj=bytesio, mode='r') as gz:
            return gz.read()

    @mock.patch('importlib.import_module')
    def test_gzip_compression(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo',
                                 'HTTP_ACCEPT_ENCODING': 'gzip,deflate'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = \
            [packet.Packet(packet.MESSAGE, data='hello')]
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertIn(('Content-Encoding', 'gzip'), headers)
        self._gzip_decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    def test_deflate_compression(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo',
                                 'HTTP_ACCEPT_ENCODING': 'deflate;q=1,gzip'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = \
            [packet.Packet(packet.MESSAGE, data='hello')]
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertIn(('Content-Encoding', 'deflate'), headers)
        zlib.decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    def test_gzip_compression_threshold(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo',
                                 'HTTP_ACCEPT_ENCODING': 'gzip'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(compression_threshold=1000)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = \
            [packet.Packet(packet.MESSAGE, data='hello')]
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress,
                          a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    def test_compression_disabled(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo',
                                 'HTTP_ACCEPT_ENCODING': 'gzip'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(http_compression=False,
                                       compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = \
            [packet.Packet(packet.MESSAGE, data='hello')]
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress,
                          a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    def test_compression_unknown(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo',
                                 'HTTP_ACCEPT_ENCODING': 'rar'})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = \
            [packet.Packet(packet.MESSAGE, data='hello')]
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress,
                          a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    def test_compression_no_encoding(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET',
                                 'QUERY_STRING': 'sid=foo',
                                 'HTTP_ACCEPT_ENCODING': ''})
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.mock.return_value = \
            [packet.Packet(packet.MESSAGE, data='hello')]
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress,
                          a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    def test_cookie(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(cookie='sid')
        s._generate_id = mock.MagicMock(return_value='123')
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        self.assertIn(('Set-Cookie', 'sid=123'), headers)

    @mock.patch('importlib.import_module')
    def test_no_cookie(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(cookie=None)
        s._generate_id = mock.MagicMock(return_value='123')
        _run(s.handle_request('request'))
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            self.assertNotEqual(header, 'Set-Cookie')

    def test_logger(self):
        s = asyncio_server.AsyncServer(logger=False)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.ERROR)
        s.logger.setLevel(logging.NOTSET)
        s = asyncio_server.AsyncServer(logger=True)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.INFO)
        s.logger.setLevel(logging.WARNING)
        s = asyncio_server.AsyncServer(logger=True)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.WARNING)
        s.logger.setLevel(logging.NOTSET)
        my_logger = logging.Logger('foo')
        s = asyncio_server.AsyncServer(logger=my_logger)
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

        asyncio_server.AsyncServer(json=CustomJSON)
        pkt = packet.Packet(packet.MESSAGE, data={'foo': 'bar'})
        self.assertEqual(pkt.encode(), b'4*** encoded ***')
        pkt2 = packet.Packet(encoded_packet=pkt.encode())
        self.assertEqual(pkt2.data, '+++ decoded +++')

        # restore the default JSON module
        packet.Packet.json = json

    def test_background_tasks(self):
        r = []

        @coroutine
        def foo(arg):
            r.append(arg)

        s = asyncio_server.AsyncServer()
        s.start_background_task(foo, 'bar')
        pending = asyncio.Task.all_tasks()
        asyncio.get_event_loop().run_until_complete(asyncio.wait(pending))
        self.assertEqual(r, ['bar'])

    def test_sleep(self):
        s = asyncio_server.AsyncServer()
        _run(s.sleep(0))

    def test_trigger_event_function(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = asyncio_server.AsyncServer()
        s.on('message', handler=foo_handler)
        _run(s._trigger_event('message', 'bar'))
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_coroutine(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = asyncio_server.AsyncServer()
        s.on('message', handler=foo_handler)
        _run(s._trigger_event('message', 'bar'))
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_function_error(self):
        def connect_handler(arg):
            return 1 / 0

        def foo_handler(arg):
            return 1 / 0

        s = asyncio_server.AsyncServer()
        s.on('connect', handler=connect_handler)
        s.on('message', handler=foo_handler)
        self.assertFalse(_run(s._trigger_event('connect', '123')))
        self.assertIsNone(_run(s._trigger_event('message', 'bar')))

    def test_trigger_event_coroutine_error(self):
        @coroutine
        def connect_handler(arg):
            return 1 / 0

        @coroutine
        def foo_handler(arg):
            return 1 / 0

        s = asyncio_server.AsyncServer()
        s.on('connect', handler=connect_handler)
        s.on('message', handler=foo_handler)
        self.assertFalse(_run(s._trigger_event('connect', '123')))
        self.assertIsNone(_run(s._trigger_event('message', 'bar')))

    def test_trigger_event_function_async(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = asyncio_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = _run(s._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_coroutine_async(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = asyncio_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = _run(s._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_function_async_error(self):
        result = []

        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        s = asyncio_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = _run(s._trigger_event('message', 'bar', run_async=True))
        self.assertRaises(
            ZeroDivisionError, asyncio.get_event_loop().run_until_complete,
            fut)
        self.assertEqual(result, ['bar'])

    def test_trigger_event_coroutine_async_error(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        s = asyncio_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = _run(s._trigger_event('message', 'bar', run_async=True))
        self.assertRaises(
            ZeroDivisionError, asyncio.get_event_loop().run_until_complete,
            fut)
        self.assertEqual(result, ['bar'])

    @mock.patch('importlib.import_module')
    def test_service_task_started(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = asyncio_server.AsyncServer(monitor_clients=True)
        s._service_task = AsyncMock()
        _run(s.handle_request('request'))
        s._service_task.mock.assert_called_once_with()
