import sys
import time
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock
try:
    import websockets
except ImportError:
    # weirdness to avoid errors in PY2 test run
    class _dummy():
        pass
    websockets = _dummy()
    websockets.exceptions = _dummy()
    websockets.exceptions.InvalidURI = _dummy()

from engineio import client
from engineio import exceptions
from engineio import packet
from engineio import payload
if sys.version_info >= (3, 5):
    import asyncio
    from asyncio import coroutine
    from engineio import asyncio_client
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
class TestAsyncClient(unittest.TestCase):
    def test_is_asyncio_based(self):
        c = asyncio_client.AsyncClient()
        self.assertEqual(c.is_asyncio_based(), True)

    def test_already_connected(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        self.assertRaises(ValueError, _run, c.connect('http://foo'))

    def test_invalid_transports(self):
        c = asyncio_client.AsyncClient()
        self.assertRaises(ValueError, _run, c.connect(
            'http://foo', transports=['foo', 'bar']))

    def test_some_invalid_transports(self):
        c = asyncio_client.AsyncClient()
        c._connect_websocket = AsyncMock()
        _run(c.connect('http://foo', transports=['foo', 'websocket', 'bar']))
        self.assertEqual(c.transports, ['websocket'])

    def test_connect_polling(self):
        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(_run(c.connect('http://foo')), 'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports=['polling'])), 'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports=['polling',
                                                     'websocket'])),
            'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_websocket(self):
        c = asyncio_client.AsyncClient()
        c._connect_websocket = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports=['websocket'])),
            'foo')
        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = asyncio_client.AsyncClient()
        c._connect_websocket = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports='websocket')),
            'foo')
        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_query_string(self):
        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(_run(c.connect('http://foo?bar=baz')), 'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo?bar=baz', {}, 'engine.io')

    def test_connect_custom_headers(self):
        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', headers={'Foo': 'Bar'})),
            'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {'Foo': 'Bar'}, 'engine.io')

    def test_wait(self):
        c = asyncio_client.AsyncClient()
        done = []

        @coroutine
        def fake_read_look_task():
            done.append(True)

        c.read_loop_task = fake_read_look_task()
        _run(c.wait())
        self.assertEqual(done, [True])

    def test_wait_no_task(self):
        c = asyncio_client.AsyncClient()
        c.read_loop_task = None
        _run(c.wait())

    def test_send(self):
        c = asyncio_client.AsyncClient()
        saved_packets = []

        @coroutine
        def fake_send_packet(pkt):
            saved_packets.append(pkt)

        c._send_packet = fake_send_packet
        _run(c.send('foo'))
        _run(c.send('foo', binary=False))
        _run(c.send(b'foo', binary=True))
        self.assertEqual(saved_packets[0].packet_type, packet.MESSAGE)
        self.assertEqual(saved_packets[0].data, 'foo')
        self.assertEqual(saved_packets[0].binary,
                         False if six.PY3 else True)
        self.assertEqual(saved_packets[1].packet_type, packet.MESSAGE)
        self.assertEqual(saved_packets[1].data, 'foo')
        self.assertEqual(saved_packets[1].binary, False)
        self.assertEqual(saved_packets[2].packet_type, packet.MESSAGE)
        self.assertEqual(saved_packets[2].data, b'foo')
        self.assertEqual(saved_packets[2].binary, True)

    def test_disconnect_not_connected(self):
        c = asyncio_client.AsyncClient()
        c.state = 'foo'
        _run(c.disconnect())
        self.assertEqual(c.state, 'disconnected')

    def test_disconnect_polling(self):
        c = asyncio_client.AsyncClient()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        c._trigger_event = AsyncMock()
        _run(c.disconnect())
        c.ws.close.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)
        c._trigger_event.mock.assert_called_once_with('disconnect')

    def test_disconnect_websocket(self):
        c = asyncio_client.AsyncClient()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        c._trigger_event = AsyncMock()
        _run(c.disconnect())
        c.ws.close.mock.assert_called_once_with()
        self.assertNotIn(c, client.connected_clients)
        c._trigger_event.mock.assert_called_once_with('disconnect')

    def test_disconnect_polling_abort(self):
        c = asyncio_client.AsyncClient()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        _run(c.disconnect(abort=True))
        c.queue.join.mock.assert_not_called()
        c.ws.close.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)

    def test_disconnect_websocket_abort(self):
        c = asyncio_client.AsyncClient()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        _run(c.disconnect(abort=True))
        c.queue.join.mock.assert_not_called()
        c.ws.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)

    def test_background_tasks(self):
        r = []

        @coroutine
        def foo(arg):
            r.append(arg)

        c = asyncio_client.AsyncClient()
        c.start_background_task(foo, 'bar')
        pending = asyncio.Task.all_tasks()
        asyncio.get_event_loop().run_until_complete(asyncio.wait(pending))
        self.assertEqual(r, ['bar'])

    def test_sleep(self):
        c = asyncio_client.AsyncClient()
        _run(c.sleep(0))

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_polling_connection_failed(self, _time):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock(return_value=None)
        self.assertRaises(
            exceptions.ConnectionError, _run, c.connect(
                'http://foo', headers={'Foo': 'Bar'}))
        c._send_request.mock.assert_called_once_with(
            'GET', 'http://foo/engine.io/?transport=polling&EIO=3&t=123.456',
            headers={'Foo': 'Bar'})

    def test_polling_connection_404(self):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 404
        self.assertRaises(
            exceptions.ConnectionError, _run, c.connect('http://foo'))

    def test_polling_connection_invalid_packet(self):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=b'foo')
        self.assertRaises(
            exceptions.ConnectionError, _run, c.connect('http://foo'))

    def test_polling_connection_no_open_packet(self):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(packets=[
                packet.Packet(packet.CLOSE, {
                    'sid': '123', 'upgrades': [], 'pingInterval': 10,
                    'pingTimeout': 20
                })
            ]).encode())
        self.assertRaises(
            exceptions.ConnectionError, _run, c.connect('http://foo'))

    def test_polling_connection_successful(self):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(packets=[
                packet.Packet(packet.OPEN, {
                    'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                    'pingTimeout': 2000
                })
            ]).encode())
        c._ping_loop = AsyncMock()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = AsyncMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))
        time.sleep(0.1)

        c._ping_loop.mock.assert_called_once_with()
        c._read_loop_polling.mock.assert_called_once_with()
        c._read_loop_websocket.mock.assert_not_called()
        c._write_loop.mock.assert_called_once_with()
        on_connect.mock.assert_called_once_with()
        self.assertIn(c, client.connected_clients)
        self.assertEqual(
            c.base_url,
            'http://foo/engine.io/?transport=polling&EIO=3&sid=123')
        self.assertEqual(c.sid, '123')
        self.assertEqual(c.ping_interval, 1)
        self.assertEqual(c.ping_timeout, 2)
        self.assertEqual(c.upgrades, [])
        self.assertEqual(c.transport(), 'polling')

    def test_polling_connection_with_more_packets(self):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(packets=[
                packet.Packet(packet.OPEN, {
                    'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                    'pingTimeout': 2000
                }),
                packet.Packet(packet.NOOP)
            ]).encode())
        c._ping_loop = AsyncMock()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        c._receive_packet = AsyncMock()
        on_connect = AsyncMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))
        time.sleep(0.1)
        self.assertEqual(c._receive_packet.mock.call_count, 1)
        self.assertEqual(
            c._receive_packet.mock.call_args_list[0][0][0].packet_type,
            packet.NOOP)

    def test_polling_connection_upgraded(self):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(packets=[
                packet.Packet(packet.OPEN, {
                    'sid': '123', 'upgrades': ['websocket'],
                    'pingInterval': 1000, 'pingTimeout': 2000
                })
            ]).encode())
        c._connect_websocket = AsyncMock(return_value=True)
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))

        c._connect_websocket.mock.assert_called_once_with('http://foo', {},
                                                          'engine.io')
        on_connect.assert_called_once_with()
        self.assertIn(c, client.connected_clients)
        self.assertEqual(
            c.base_url,
            'http://foo/engine.io/?transport=polling&EIO=3&sid=123')
        self.assertEqual(c.sid, '123')
        self.assertEqual(c.ping_interval, 1)
        self.assertEqual(c.ping_timeout, 2)
        self.assertEqual(c.upgrades, ['websocket'])

    def test_polling_connection_not_upgraded(self):
        c = asyncio_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(packets=[
                packet.Packet(packet.OPEN, {
                    'sid': '123', 'upgrades': ['websocket'],
                    'pingInterval': 1000, 'pingTimeout': 2000
                })
            ]).encode())
        c._connect_websocket = AsyncMock(return_value=False)
        c._ping_loop = AsyncMock()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))
        time.sleep(0.1)

        c._connect_websocket.mock.assert_called_once_with('http://foo', {},
                                                          'engine.io')
        c._ping_loop.mock.assert_called_once_with()
        c._read_loop_polling.mock.assert_called_once_with()
        c._read_loop_websocket.mock.assert_not_called()
        c._write_loop.mock.assert_called_once_with()
        on_connect.assert_called_once_with()
        self.assertIn(c, client.connected_clients)

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch('engineio.asyncio_client.websockets.connect', new=AsyncMock(
        side_effect=[websockets.exceptions.InvalidURI]))
    def test_websocket_connection_failed(self, _time):
        c = asyncio_client.AsyncClient()
        self.assertRaises(
            exceptions.ConnectionError, _run,
            c.connect('http://foo', transports=['websocket'],
                      headers={'Foo': 'Bar'}))
        asyncio_client.websockets.connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=3&t=123.456',
            extra_headers={'Foo': 'Bar'})

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch('engineio.asyncio_client.websockets.connect', new=AsyncMock(
        side_effect=[websockets.exceptions.InvalidURI]))
    def test_websocket_upgrade_failed(self, _time):
        c = asyncio_client.AsyncClient()
        c.sid = '123'
        self.assertFalse(_run(c.connect(
            'http://foo', transports=['websocket'])))
        asyncio_client.websockets.connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=3&sid=123&t=123.456',
            extra_headers={})

    @mock.patch('engineio.asyncio_client.websockets.connect', new=AsyncMock())
    def test_websocket_connection_no_open_packet(self):
        asyncio_client.websockets.connect.mock.return_value.recv = AsyncMock(
            return_value=packet.Packet(packet.CLOSE).encode())
        c = asyncio_client.AsyncClient()
        self.assertRaises(
            exceptions.ConnectionError, _run,
            c.connect('http://foo', transports=['websocket']))

    @mock.patch('engineio.asyncio_client.websockets.connect', new=AsyncMock())
    def test_websocket_connection_successful(self):
        ws = asyncio_client.websockets.connect.mock.return_value
        ws.recv = AsyncMock(return_value=packet.Packet(
            packet.OPEN, {
                'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                'pingTimeout': 2000
            }).encode())
        c = asyncio_client.AsyncClient()
        c._ping_loop = AsyncMock()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('ws://foo', transports=['websocket']))
        time.sleep(0.1)

        c._ping_loop.mock.assert_called_once_with()
        c._read_loop_polling.mock.assert_not_called()
        c._read_loop_websocket.mock.assert_called_once_with()
        c._write_loop.mock.assert_called_once_with()
        on_connect.assert_called_once_with()
        self.assertIn(c, client.connected_clients)
        self.assertEqual(
            c.base_url,
            'ws://foo/engine.io/?transport=websocket&EIO=3')
        self.assertEqual(c.sid, '123')
        self.assertEqual(c.ping_interval, 1)
        self.assertEqual(c.ping_timeout, 2)
        self.assertEqual(c.upgrades, [])
        self.assertEqual(c.transport(), 'websocket')
        self.assertEqual(c.ws, ws)

    @mock.patch('engineio.asyncio_client.websockets.connect', new=AsyncMock())
    def test_websocket_upgrade_no_pong(self):
        ws = asyncio_client.websockets.connect.mock.return_value
        ws.recv = AsyncMock(return_value=packet.Packet(
            packet.OPEN, {
                'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                'pingTimeout': 2000
            }).encode())
        ws.send = AsyncMock()
        c = asyncio_client.AsyncClient()
        c.sid = '123'
        c.current_transport = 'polling'
        c._ping_loop = AsyncMock()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        self.assertFalse(_run(c.connect('ws://foo',
                                        transports=['websocket'])))

        c._ping_loop.mock.assert_not_called()
        c._read_loop_polling.mock.assert_not_called()
        c._read_loop_websocket.mock.assert_not_called()
        c._write_loop.mock.assert_not_called()
        on_connect.assert_not_called()
        self.assertEqual(c.transport(), 'polling')
        ws.send.mock.assert_called_once_with('2probe')

    @mock.patch('engineio.asyncio_client.websockets.connect', new=AsyncMock())
    def test_websocket_upgrade_successful(self):
        ws = asyncio_client.websockets.connect.mock.return_value
        ws.recv = AsyncMock(return_value=packet.Packet(
            packet.PONG, 'probe').encode())
        ws.send = AsyncMock()
        c = asyncio_client.AsyncClient()
        c.sid = '123'
        c.base_url = 'http://foo'
        c.current_transport = 'polling'
        c._ping_loop = AsyncMock()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        self.assertTrue(_run(c.connect('ws://foo',
                                       transports=['websocket'])))
        time.sleep(0.1)

        c._ping_loop.mock.assert_called_once_with()
        c._read_loop_polling.mock.assert_not_called()
        c._read_loop_websocket.mock.assert_called_once_with()
        c._write_loop.mock.assert_called_once_with()
        on_connect.assert_not_called()  # was called by polling
        self.assertNotIn(c, client.connected_clients)  # was added by polling
        self.assertEqual(c.base_url, 'http://foo')  # not changed
        self.assertEqual(c.sid, '123')  # not changed
        self.assertEqual(c.transport(), 'websocket')
        self.assertEqual(c.ws, ws)
        self.assertEqual(
            ws.send.mock.call_args_list[0],
            (('2probe',),))  # ping
        self.assertEqual(
            ws.send.mock.call_args_list[1],
            (('5',),))  # upgrade

    def test_receive_unknown_packet(self):
        c = asyncio_client.AsyncClient()
        _run(c._receive_packet(packet.Packet(encoded_packet=b'9')))
        # should be ignored

    def test_receive_noop_packet(self):
        c = asyncio_client.AsyncClient()
        _run(c._receive_packet(packet.Packet(packet.NOOP)))
        # should be ignored

    def test_receive_pong_packet(self):
        c = asyncio_client.AsyncClient()
        c.pong_received = False
        _run(c._receive_packet(packet.Packet(packet.PONG)))
        self.assertTrue(c.pong_received)

    def test_receive_message_packet(self):
        c = asyncio_client.AsyncClient()
        on_message = AsyncMock()
        c.on('message', on_message)
        _run(c._receive_packet(packet.Packet(packet.MESSAGE, {'foo': 'bar'})))
        on_message.mock.assert_called_once_with({'foo': 'bar'})

    def test_send_packet_disconnected(self):
        c = asyncio_client.AsyncClient()
        c.queue, c.queue_empty = c._create_queue()
        c.state = 'disconnected'
        _run(c._send_packet(packet.Packet(packet.NOOP)))
        self.assertTrue(c.queue.empty())

    def test_send_packet(self):
        c = asyncio_client.AsyncClient()
        c.queue, c.queue_empty = c._create_queue()
        c.state = 'connected'
        _run(c._send_packet(packet.Packet(packet.NOOP)))
        self.assertFalse(c.queue.empty())
        pkt = _run(c.queue.get())
        self.assertEqual(pkt.packet_type, packet.NOOP)

    def test_trigger_event_function(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        _run(c._trigger_event('message', 'bar'))
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_coroutine(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        _run(c._trigger_event('message', 'bar'))
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_function_error(self):
        def connect_handler(arg):
            return 1 / 0

        def foo_handler(arg):
            return 1 / 0

        c = asyncio_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        self.assertFalse(_run(c._trigger_event('connect', '123')))
        self.assertIsNone(_run(c._trigger_event('message', 'bar')))

    def test_trigger_event_coroutine_error(self):
        @coroutine
        def connect_handler(arg):
            return 1 / 0

        @coroutine
        def foo_handler(arg):
            return 1 / 0

        c = asyncio_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        self.assertFalse(_run(c._trigger_event('connect', '123')))
        self.assertIsNone(_run(c._trigger_event('message', 'bar')))

    def test_trigger_event_function_async(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_coroutine_async(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_function_async_error(self):
        result = []

        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
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

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        self.assertRaises(
            ZeroDivisionError, asyncio.get_event_loop().run_until_complete,
            fut)
        self.assertEqual(result, ['bar'])

    def test_trigger_unknown_event(self):
        c = asyncio_client.AsyncClient()
        _run(c._trigger_event('connect', run_async=False))
        _run(c._trigger_event('message', 123, run_async=True))
        # should do nothing

    def test_ping_loop_disconnected(self):
        c = asyncio_client.AsyncClient()
        c.state = 'disconnected'
        _run(c._ping_loop())
        # should not block

    def test_ping_loop_disconnect(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 10
        c._send_packet = AsyncMock()

        states = [
            ('disconnecting', True)
        ]

        @coroutine
        def fake_wait():
            c.state, c.pong_received = states.pop(0)

        c.ping_loop_event.wait = fake_wait
        _run(c._ping_loop())
        self.assertEqual(
            c._send_packet.mock.call_args_list[0][0][0].encode(), b'2')

    def test_ping_loop_missing_pong(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 10
        c._send_packet = AsyncMock()
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()

        states = [
            ('connected', False)
        ]

        @coroutine
        def fake_wait():
            c.state, c.pong_received = states.pop(0)

        c.ping_loop_event.wait = fake_wait
        _run(c._ping_loop())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)

    def test_ping_loop_missing_pong_websocket(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 10
        c._send_packet = AsyncMock()
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()

        states = [
            ('connected', False)
        ]

        @coroutine
        def fake_wait():
            c.state, c.pong_received = states.pop(0)

        c.ping_loop_event.wait = fake_wait
        _run(c._ping_loop())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)
        c.ws.close.mock.assert_called_once_with()

    def test_read_loop_polling_disconnected(self):
        c = asyncio_client.AsyncClient()
        c.state = 'disconnected'
        c._trigger_event = AsyncMock()
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        c._trigger_event.mock.assert_not_called()
        # should not block

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_no_response(self, _time):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock(return_value=None)
        c._trigger_event = AsyncMock()
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)
        c._send_request.mock.assert_called_once_with(
            'GET', 'http://foo&t=123.456')
        c._trigger_event.mock.assert_called_once_with('disconnect')

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_status(self, _time):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 400
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)
        c._send_request.mock.assert_called_once_with(
            'GET', 'http://foo&t=123.456')

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_packet(self, _time):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=b'foo')
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)
        c._send_request.mock.assert_called_once_with(
            'GET', 'http://foo&t=123.456')

    def test_read_loop_polling(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock()
        c._send_request.mock.side_effect = [
            mock.MagicMock(status=200, read=AsyncMock(
                return_value=payload.Payload(packets=[
                    packet.Packet(packet.PING),
                    packet.Packet(packet.NOOP)]).encode())),
            None
        ]
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        c._receive_packet = AsyncMock()
        _run(c._read_loop_polling())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)
        self.assertEqual(c._send_request.mock.call_count, 2)
        self.assertEqual(c._receive_packet.mock.call_count, 2)
        self.assertEqual(
            c._receive_packet.mock.call_args_list[0][0][0].encode(), b'2')
        self.assertEqual(
            c._receive_packet.mock.call_args_list[1][0][0].encode(), b'6')

    def test_read_loop_websocket_disconnected(self):
        c = asyncio_client.AsyncClient()
        c.state = 'disconnected'
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        _run(c._read_loop_websocket())
        # should not block

    def test_read_loop_websocket_no_response(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.recv = AsyncMock(
            side_effect=websockets.exceptions.ConnectionClosed(1, 'foo'))
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        _run(c._read_loop_websocket())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)

    def test_read_loop_websocket_unexpected_error(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.recv = AsyncMock(side_effect=ValueError)
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        _run(c._read_loop_websocket())
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.mock.assert_called_once_with(None)

    def test_read_loop_websocket(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.recv = AsyncMock(side_effect=[
            packet.Packet(packet.PING).encode(), ValueError])
        c.write_loop_task = AsyncMock()()
        c.ping_loop_task = AsyncMock()()
        c._receive_packet = AsyncMock()
        _run(c._read_loop_websocket())
        self.assertEqual(c.state, 'disconnected')
        self.assertEqual(
            c._receive_packet.mock.call_args_list[0][0][0].encode(), b'2')
        c.queue.put.mock.assert_called_once_with(None)

    def test_write_loop_disconnected(self):
        c = asyncio_client.AsyncClient()
        c.state = 'disconnected'
        _run(c._write_loop())
        # should not block

    def test_write_loop_no_packets(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.get = AsyncMock(return_value=None)
        _run(c._write_loop())
        c.queue.task_done.assert_called_once_with()
        c.queue.get.mock.assert_called_once_with()

    def test_write_loop_empty_queue(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=RuntimeError)
        _run(c._write_loop())
        c.queue.get.mock.assert_called_once_with()

    def test_write_loop_polling_one_packet(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=RuntimeError)
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        _run(c._write_loop())
        self.assertEqual(c.queue.task_done.call_count, 1)
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})])
        c._send_request.mock.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})

    def test_write_loop_polling_three_packets(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=[
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
            RuntimeError
        ])
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        _run(c._write_loop())
        self.assertEqual(c.queue.task_done.call_count, 3)
        p = payload.Payload(packets=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
        ])
        c._send_request.mock.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})

    def test_write_loop_polling_two_packets_done(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=[
            packet.Packet(packet.PING),
            None
        ])
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        _run(c._write_loop())
        self.assertEqual(c.queue.task_done.call_count, 3)
        p = payload.Payload(packets=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
        ])
        c._send_request.mock.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(c.state, 'disconnected')

    def test_write_loop_polling_bad_connection(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=[
            RuntimeError
        ])
        c._send_request = AsyncMock(return_value=None)
        _run(c._write_loop())
        self.assertEqual(c.queue.task_done.call_count, 1)
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})])
        c._send_request.mock.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(c.state, 'disconnected')

    def test_write_loop_polling_bad_status(self):
        c = asyncio_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=[
            RuntimeError
        ])
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 500
        _run(c._write_loop())
        self.assertEqual(c.queue.task_done.call_count, 1)
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})])
        c._send_request.mock.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(c.state, 'disconnected')

    def test_write_loop_websocket_one_packet(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=[
            RuntimeError
        ])
        c.ws = mock.MagicMock()
        c.ws.send = AsyncMock()
        _run(c._write_loop())
        self.assertEqual(c.queue.task_done.call_count, 1)
        self.assertEqual(c.ws.send.mock.call_count, 1)
        c.ws.send.mock.assert_called_once_with('4{"foo":"bar"}')

    def test_write_loop_websocket_three_packets(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=[
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
            RuntimeError
        ])
        c.ws = mock.MagicMock()
        c.ws.send = AsyncMock()
        _run(c._write_loop())
        self.assertEqual(c.queue.task_done.call_count, 3)
        self.assertEqual(c.ws.send.mock.call_count, 3)
        self.assertEqual(c.ws.send.mock.call_args_list[0][0][0],
                         '4{"foo":"bar"}')
        self.assertEqual(c.ws.send.mock.call_args_list[1][0][0], '2')
        self.assertEqual(c.ws.send.mock.call_args_list[2][0][0], '6')

    def test_write_loop_websocket_bad_connection(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError
        ])
        c.queue.get_nowait = mock.MagicMock(side_effect=[
            RuntimeError
        ])
        c.ws = mock.MagicMock()
        c.ws.send = AsyncMock(
            side_effect=websockets.exceptions.ConnectionClosed(1, 'foo'))
        _run(c._write_loop())
        self.assertEqual(c.state, 'disconnected')
