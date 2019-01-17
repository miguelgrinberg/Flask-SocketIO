import json
import logging
import time
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock
import websocket

from engineio import client
from engineio import exceptions
from engineio import packet
from engineio import payload

if six.PY2:
    ConnectionError = OSError


class TestClient(unittest.TestCase):
    def test_is_asyncio_based(self):
        c = client.Client()
        self.assertEqual(c.is_asyncio_based(), False)

    def test_create(self):
        c = client.Client()
        self.assertEqual(c.handlers, {})
        for attr in ['base_url', 'transports', 'sid', 'upgrades',
                     'ping_interval', 'ping_timeout', 'http', 'ws',
                     'read_loop_task', 'write_loop_task', 'queue',
                     'queue_empty']:
            self.assertIsNone(getattr(c, attr), attr + ' is not None')
        self.assertTrue(c.pong_received)
        self.assertEqual(c.state, 'disconnected')

    def test_custon_json(self):
        client.Client()
        self.assertEqual(packet.Packet.json, json)
        client.Client(json='foo')
        self.assertEqual(packet.Packet.json, 'foo')
        packet.Packet.json = json

    def test_logger(self):
        c = client.Client(logger=False)
        self.assertEqual(c.logger.getEffectiveLevel(), logging.ERROR)
        c.logger.setLevel(logging.NOTSET)
        c = client.Client(logger=True)
        self.assertEqual(c.logger.getEffectiveLevel(), logging.INFO)
        c.logger.setLevel(logging.WARNING)
        c = client.Client(logger=True)
        self.assertEqual(c.logger.getEffectiveLevel(), logging.WARNING)
        c.logger.setLevel(logging.NOTSET)
        my_logger = logging.Logger('foo')
        c = client.Client(logger=my_logger)
        self.assertEqual(c.logger, my_logger)

    def test_on_event(self):
        c = client.Client()

        @c.on('connect')
        def foo():
            pass
        c.on('disconnect', foo)

        self.assertEqual(c.handlers['connect'], foo)
        self.assertEqual(c.handlers['disconnect'], foo)

    def test_on_event_invalid(self):
        c = client.Client()
        self.assertRaises(ValueError, c.on, 'invalid')

    def test_already_connected(self):
        c = client.Client()
        c.state = 'connected'
        self.assertRaises(ValueError, c.connect, 'http://foo')

    def test_invalid_transports(self):
        c = client.Client()
        self.assertRaises(ValueError, c.connect, 'http://foo',
                          transports=['foo', 'bar'])

    def test_some_invalid_transports(self):
        c = client.Client()
        c._connect_websocket = mock.MagicMock()
        c.connect('http://foo', transports=['foo', 'websocket', 'bar'])
        self.assertEqual(c.transports, ['websocket'])

    def test_connect_polling(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo'), 'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', transports=['polling']),
                         'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo',
                                   transports=['polling', 'websocket']),
                         'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_websocket(self):
        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', transports=['websocket']),
                         'foo')
        c._connect_websocket.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', transports='websocket'),
                         'foo')
        c._connect_websocket.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_query_string(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo?bar=baz'), 'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo?bar=baz', {}, 'engine.io')

    def test_connect_custom_headers(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', headers={'Foo': 'Bar'}),
                         'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {'Foo': 'Bar'}, 'engine.io')

    def test_wait(self):
        c = client.Client()
        c.read_loop_task = mock.MagicMock()
        c.wait()
        c.read_loop_task.join.assert_called_once_with()

    def test_wait_no_task(self):
        c = client.Client()
        c.read_loop_task = None
        c.wait()  # should not block

    def test_send(self):
        c = client.Client()
        saved_packets = []

        def fake_send_packet(pkt):
            saved_packets.append(pkt)

        c._send_packet = fake_send_packet
        c.send('foo')
        c.send('foo', binary=False)
        c.send(b'foo', binary=True)
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
        c = client.Client()
        c.state = 'foo'
        c.disconnect()
        self.assertEqual(c.state, 'disconnected')

    def test_disconnect_polling(self):
        c = client.Client()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c._trigger_event = mock.MagicMock()
        c.disconnect()
        c.read_loop_task.join.assert_called_once_with()
        c.ws.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)
        c._trigger_event.assert_called_once_with('disconnect')

    def test_disconnect_websocket(self):
        c = client.Client()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c._trigger_event = mock.MagicMock()
        c.disconnect()
        c.read_loop_task.join.assert_called_once_with()
        c.ws.close.assert_called_once_with()
        self.assertNotIn(c, client.connected_clients)
        c._trigger_event.assert_called_once_with('disconnect')

    def test_disconnect_polling_abort(self):
        c = client.Client()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.disconnect(abort=True)
        c.queue.join.assert_not_called()
        c.read_loop_task.join.assert_not_called()
        c.ws.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)

    def test_disconnect_websocket_abort(self):
        c = client.Client()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.disconnect(abort=True)
        c.queue.join.assert_not_called()
        c.read_loop_task.join.assert_not_called()
        c.ws.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)

    def test_current_transport(self):
        c = client.Client()
        c.current_transport = 'foo'
        self.assertEqual(c.transport(), 'foo')

    def test_background_tasks(self):
        flag = {}

        def bg_task():
            flag['task'] = True

        c = client.Client()
        task = c.start_background_task(bg_task)
        task.join()
        self.assertIn('task', flag)
        self.assertTrue(flag['task'])

    def test_sleep(self):
        c = client.Client()
        t = time.time()
        c.sleep(0.1)
        self.assertTrue(time.time() - t > 0.1)

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch('engineio.client.Client._send_request', return_value=None)
    def test_polling_connection_failed(self, _send_request, _time):
        c = client.Client()
        self.assertRaises(exceptions.ConnectionError, c.connect, 'http://foo',
                          headers={'Foo': 'Bar'})
        _send_request.assert_called_once_with(
            'GET', 'http://foo/engine.io/?transport=polling&EIO=3&t=123.456',
            headers={'Foo': 'Bar'})

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_404(self, _send_request):
        _send_request.return_value.status = 404
        c = client.Client()
        self.assertRaises(exceptions.ConnectionError, c.connect, 'http://foo')

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_invalid_packet(self, _send_request):
        _send_request.return_value.status = 200
        _send_request.return_value.data = b'foo'
        c = client.Client()
        self.assertRaises(exceptions.ConnectionError, c.connect, 'http://foo')

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_no_open_packet(self, _send_request):
        _send_request.return_value.status = 200
        _send_request.return_value.data = payload.Payload(packets=[
            packet.Packet(packet.CLOSE, {
                'sid': '123', 'upgrades': [], 'pingInterval': 10,
                'pingTimeout': 20
            })
        ]).encode()
        c = client.Client()
        self.assertRaises(exceptions.ConnectionError, c.connect, 'http://foo')

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_successful(self, _send_request):
        _send_request.return_value.status = 200
        _send_request.return_value.data = payload.Payload(packets=[
            packet.Packet(packet.OPEN, {
                'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                'pingTimeout': 2000
            })
        ]).encode()
        c = client.Client()
        c._ping_loop = mock.MagicMock()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')
        time.sleep(0.1)

        c._ping_loop.assert_called_once_with()
        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
        self.assertIn(c, client.connected_clients)
        self.assertEqual(
            c.base_url,
            'http://foo/engine.io/?transport=polling&EIO=3&sid=123')
        self.assertEqual(c.sid, '123')
        self.assertEqual(c.ping_interval, 1)
        self.assertEqual(c.ping_timeout, 2)
        self.assertEqual(c.upgrades, [])
        self.assertEqual(c.transport(), 'polling')

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_with_more_packets(self, _send_request):
        _send_request.return_value.status = 200
        _send_request.return_value.data = payload.Payload(packets=[
            packet.Packet(packet.OPEN, {
                'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                'pingTimeout': 2000
            }),
            packet.Packet(packet.NOOP)
        ]).encode()
        c = client.Client()
        c._ping_loop = mock.MagicMock()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        c._receive_packet = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')
        time.sleep(0.1)
        self.assertEqual(c._receive_packet.call_count, 1)
        self.assertEqual(
            c._receive_packet.call_args_list[0][0][0].packet_type,
            packet.NOOP)

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_upgraded(self, _send_request):
        _send_request.return_value.status = 200
        _send_request.return_value.data = payload.Payload(packets=[
            packet.Packet(packet.OPEN, {
                'sid': '123', 'upgrades': ['websocket'], 'pingInterval': 1000,
                'pingTimeout': 2000
            })
        ]).encode()
        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value=True)
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')

        c._connect_websocket.assert_called_once_with('http://foo', {},
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

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_not_upgraded(self, _send_request):
        _send_request.return_value.status = 200
        _send_request.return_value.data = payload.Payload(packets=[
            packet.Packet(packet.OPEN, {
                'sid': '123', 'upgrades': ['websocket'], 'pingInterval': 1000,
                'pingTimeout': 2000
            })
        ]).encode()
        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value=False)
        c._ping_loop = mock.MagicMock()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')
        time.sleep(0.1)

        c._connect_websocket.assert_called_once_with('http://foo', {},
                                                     'engine.io')
        c._ping_loop.assert_called_once_with()
        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
        self.assertIn(c, client.connected_clients)

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch('engineio.client.websocket.create_connection',
                side_effect=[ConnectionError])
    def test_websocket_connection_failed(self, create_connection, _time):
        c = client.Client()
        self.assertRaises(exceptions.ConnectionError, c.connect, 'http://foo',
                          transports=['websocket'], headers={'Foo': 'Bar'})
        create_connection.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=3&t=123.456',
            header={'Foo': 'Bar'})

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch('engineio.client.websocket.create_connection',
                side_effect=[ConnectionError])
    def test_websocket_upgrade_failed(self, create_connection, _time):
        c = client.Client()
        c.sid = '123'
        self.assertFalse(c.connect('http://foo', transports=['websocket']))
        create_connection.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=3&sid=123&t=123.456',
            header={})

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_no_open_packet(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.CLOSE).encode()
        c = client.Client()
        self.assertRaises(exceptions.ConnectionError, c.connect, 'http://foo',
                          transports=['websocket'])

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_successful(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN, {
                'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                'pingTimeout': 2000
            }).encode()
        c = client.Client()
        c._ping_loop = mock.MagicMock()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])
        time.sleep(0.1)

        c._ping_loop.assert_called_once_with()
        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_called_once_with()
        c._write_loop.assert_called_once_with()
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
        self.assertEqual(c.ws, create_connection.return_value)

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_upgrade_no_pong(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN, {
                'sid': '123', 'upgrades': [], 'pingInterval': 1000,
                'pingTimeout': 2000
            }).encode()
        c = client.Client()
        c.sid = '123'
        c.current_transport = 'polling'
        c._ping_loop = mock.MagicMock()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        self.assertFalse(c.connect('ws://foo', transports=['websocket']))

        c._ping_loop.assert_not_called()
        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_not_called()
        on_connect.assert_not_called()
        self.assertEqual(c.transport(), 'polling')

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_upgrade_successful(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.PONG, 'probe').encode()
        c = client.Client()
        c.sid = '123'
        c.base_url = 'http://foo'
        c.current_transport = 'polling'
        c._ping_loop = mock.MagicMock()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        self.assertTrue(c.connect('ws://foo', transports=['websocket']))
        time.sleep(0.1)

        c._ping_loop.assert_called_once_with()
        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_called_once_with()
        c._write_loop.assert_called_once_with()
        on_connect.assert_not_called()  # was called by polling
        self.assertNotIn(c, client.connected_clients)  # was added by polling
        self.assertEqual(c.base_url, 'http://foo')  # not changed
        self.assertEqual(c.sid, '123')  # not changed
        self.assertEqual(c.transport(), 'websocket')
        self.assertEqual(c.ws, create_connection.return_value)
        self.assertEqual(
            create_connection.return_value.send.call_args_list[0],
            ((packet.Packet(packet.PING, 'probe').encode(),),))  # ping
        self.assertEqual(
            create_connection.return_value.send.call_args_list[1],
            ((packet.Packet(packet.UPGRADE).encode(),),))  # upgrade

    def test_receive_unknown_packet(self):
        c = client.Client()
        c._receive_packet(packet.Packet(encoded_packet=b'9'))
        # should be ignored

    def test_receive_noop_packet(self):
        c = client.Client()
        c._receive_packet(packet.Packet(packet.NOOP))
        # should be ignored

    def test_receive_pong_packet(self):
        c = client.Client()
        c.pong_received = False
        c._receive_packet(packet.Packet(packet.PONG))
        self.assertTrue(c.pong_received)

    def test_receive_message_packet(self):
        c = client.Client()
        on_message = mock.MagicMock()
        c.on('message', on_message)
        c._receive_packet(packet.Packet(packet.MESSAGE, {'foo': 'bar'}))
        on_message.assert_called_once_with({'foo': 'bar'})

    def test_send_packet_disconnected(self):
        c = client.Client()
        c.queue, c.queue_empty = c._create_queue()
        c.state = 'disconnected'
        c._send_packet(packet.Packet(packet.NOOP))
        self.assertTrue(c.queue.empty())

    def test_send_packet(self):
        c = client.Client()
        c.queue, c.queue_empty = c._create_queue()
        c.state = 'connected'
        c._send_packet(packet.Packet(packet.NOOP))
        self.assertFalse(c.queue.empty())
        pkt = c.queue.get()
        self.assertEqual(pkt.packet_type, packet.NOOP)

    def test_trigger_event(self):
        c = client.Client()
        f = {}

        @c.on('connect')
        def foo():
            return 'foo'

        @c.on('message')
        def bar(data):
            f['bar'] = data
            return 'bar'

        r = c._trigger_event('connect', run_async=False)
        self.assertEqual(r, 'foo')
        r = c._trigger_event('message', 123, run_async=True)
        r.join()
        self.assertEqual(f['bar'], 123)
        r = c._trigger_event('message', 321)
        self.assertEqual(r, 'bar')

    def test_trigger_unknown_event(self):
        c = client.Client()
        c._trigger_event('connect', run_async=False)
        c._trigger_event('message', 123, run_async=True)
        # should do nothing

    def test_trigger_event_error(self):
        c = client.Client()

        @c.on('connect')
        def foo():
            return 1 / 0

        @c.on('message')
        def bar(data):
            return 1 / 0

        r = c._trigger_event('connect', run_async=False)
        self.assertEqual(r, None)
        r = c._trigger_event('message', 123, run_async=False)
        self.assertEqual(r, None)

    def test_engineio_url(self):
        c = client.Client()
        self.assertEqual(
            c._get_engineio_url('http://foo', 'bar', 'polling'),
            'http://foo/bar/?transport=polling&EIO=3')
        self.assertEqual(
            c._get_engineio_url('http://foo', 'bar', 'websocket'),
            'ws://foo/bar/?transport=websocket&EIO=3')
        self.assertEqual(
            c._get_engineio_url('ws://foo', 'bar', 'polling'),
            'http://foo/bar/?transport=polling&EIO=3')
        self.assertEqual(
            c._get_engineio_url('ws://foo', 'bar', 'websocket'),
            'ws://foo/bar/?transport=websocket&EIO=3')
        self.assertEqual(
            c._get_engineio_url('https://foo', 'bar', 'polling'),
            'https://foo/bar/?transport=polling&EIO=3')
        self.assertEqual(
            c._get_engineio_url('https://foo', 'bar', 'websocket'),
            'wss://foo/bar/?transport=websocket&EIO=3')
        self.assertEqual(
            c._get_engineio_url('http://foo?baz=1', 'bar', 'polling'),
            'http://foo/bar/?baz=1&transport=polling&EIO=3')
        self.assertEqual(
            c._get_engineio_url('http://foo#baz', 'bar', 'polling'),
            'http://foo/bar/?transport=polling&EIO=3')

    def test_ping_loop_disconnected(self):
        c = client.Client()
        c.state = 'disconnected'
        c._ping_loop()
        # should not block

    def test_ping_loop_disconnect(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 10
        c._send_packet = mock.MagicMock()

        states = [
            ('disconnecting', True)
        ]

        def fake_wait(timeout):
            self.assertEqual(timeout, 10)
            c.state, c.pong_received = states.pop(0)

        c.ping_loop_event.wait = fake_wait
        c._ping_loop()
        self.assertEqual(
            c._send_packet.call_args_list[0][0][0].encode(), b'2')

    def test_ping_loop_missing_pong(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 10
        c._send_packet = mock.MagicMock()
        c.queue = mock.MagicMock()

        states = [
            ('connected', False)
        ]

        def fake_wait(timeout):
            self.assertEqual(timeout, 10)
            c.state, c.pong_received = states.pop(0)

        c.ping_loop_event.wait = fake_wait
        c._ping_loop()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)

    def test_ping_loop_missing_pong_websocket(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 10
        c._send_packet = mock.MagicMock()
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()

        states = [
            ('connected', False)
        ]

        def fake_wait(timeout):
            self.assertEqual(timeout, 10)
            c.state, c.pong_received = states.pop(0)

        c.ping_loop_event.wait = fake_wait
        c._ping_loop()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        c.ws.close.assert_called_once_with()

    def test_read_loop_polling_disconnected(self):
        c = client.Client()
        c.state = 'disconnected'
        c._trigger_event = mock.MagicMock()
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._read_loop_polling()
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()
        c._trigger_event.assert_not_called()

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_no_response(self, _time):
        c = client.Client()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock(return_value=None)
        c._trigger_event = mock.MagicMock()
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._read_loop_polling()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()
        c._send_request.assert_called_once_with('GET', 'http://foo&t=123.456')
        c._trigger_event.assert_called_once_with('disconnect')

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_status(self, _time):
        c = client.Client()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status = 400
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._read_loop_polling()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()
        c._send_request.assert_called_once_with('GET', 'http://foo&t=123.456')

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_packet(self, _time):
        c = client.Client()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.data = b'foo'
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._read_loop_polling()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()
        c._send_request.assert_called_once_with('GET', 'http://foo&t=123.456')

    def test_read_loop_polling(self):
        c = client.Client()
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock()
        c._send_request.side_effect = [
            mock.MagicMock(status=200, data=payload.Payload(packets=[
                packet.Packet(packet.PING),
                packet.Packet(packet.NOOP)]).encode()),
            None
        ]
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._receive_packet = mock.MagicMock()
        c._read_loop_polling()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        self.assertEqual(c._send_request.call_count, 2)
        self.assertEqual(c._receive_packet.call_count, 2)
        self.assertEqual(c._receive_packet.call_args_list[0][0][0].encode(),
                         b'2')
        self.assertEqual(c._receive_packet.call_args_list[1][0][0].encode(),
                         b'6')

    def test_read_loop_websocket_disconnected(self):
        c = client.Client()
        c.state = 'disconnected'
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._read_loop_websocket()
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()

    def test_read_loop_websocket_no_response(self):
        c = client.Client()
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.ws.recv.side_effect = websocket.WebSocketConnectionClosedException
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._read_loop_websocket()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()

    def test_read_loop_websocket_unexpected_error(self):
        c = client.Client()
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.ws.recv.side_effect = ValueError
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._read_loop_websocket()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()

    def test_read_loop_websocket(self):
        c = client.Client()
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.ws.recv.side_effect = [packet.Packet(packet.PING).encode(),
                                 ValueError]
        c.write_loop_task = mock.MagicMock()
        c.ping_loop_task = mock.MagicMock()
        c._receive_packet = mock.MagicMock()
        c._read_loop_websocket()
        self.assertEqual(c.state, 'disconnected')
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c.ping_loop_task.join.assert_called_once_with()
        self.assertEqual(c._receive_packet.call_args_list[0][0][0].encode(),
                         b'2')

    def test_write_loop_disconnected(self):
        c = client.Client()
        c.state = 'disconnected'
        c._write_loop()
        # should not block

    def test_write_loop_no_packets(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.get.return_value = None
        c._write_loop()
        c.queue.task_done.assert_called_once_with()
        c.queue.get.assert_called_once_with(timeout=2)

    def test_write_loop_empty_queue(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = RuntimeError
        c._write_loop()
        c.queue.get.assert_called_once_with(timeout=2)

    def test_write_loop_polling_one_packet(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
            RuntimeError
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status = 200
        c._write_loop()
        self.assertEqual(c.queue.task_done.call_count, 1)
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})])
        c._send_request.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})

    def test_write_loop_polling_three_packets(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
            RuntimeError,
            RuntimeError
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status = 200
        c._write_loop()
        self.assertEqual(c.queue.task_done.call_count, 3)
        p = payload.Payload(packets=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
        ])
        c._send_request.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})

    def test_write_loop_polling_two_packets_done(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            None,
            RuntimeError
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status = 200
        c._write_loop()
        self.assertEqual(c.queue.task_done.call_count, 3)
        p = payload.Payload(packets=[
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
        ])
        c._send_request.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(c.state, 'disconnected')

    def test_write_loop_polling_bad_connection(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value = None
        c._write_loop()
        self.assertEqual(c.queue.task_done.call_count, 1)
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})])
        c._send_request.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(c.state, 'disconnected')

    def test_write_loop_polling_bad_status(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status = 500
        c._write_loop()
        self.assertEqual(c.queue.task_done.call_count, 1)
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})])
        c._send_request.assert_called_once_with(
            'POST', 'http://foo', body=p.encode(),
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(c.state, 'disconnected')

    def test_write_loop_websocket_one_packet(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
            RuntimeError
        ]
        c.ws = mock.MagicMock()
        c._write_loop()
        self.assertEqual(c.queue.task_done.call_count, 1)
        self.assertEqual(c.ws.send.call_count, 1)
        c.ws.send.assert_called_once_with(b'4{"foo":"bar"}')

    def test_write_loop_websocket_three_packets(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
            RuntimeError,
            RuntimeError
        ]
        c.ws = mock.MagicMock()
        c._write_loop()
        self.assertEqual(c.queue.task_done.call_count, 3)
        self.assertEqual(c.ws.send.call_count, 3)
        self.assertEqual(c.ws.send.call_args_list[0][0][0], b'4{"foo":"bar"}')
        self.assertEqual(c.ws.send.call_args_list[1][0][0], b'2')
        self.assertEqual(c.ws.send.call_args_list[2][0][0], b'6')

    def test_write_loop_websocket_bad_connection(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue_empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
            RuntimeError
        ]
        c.ws = mock.MagicMock()
        c.ws.send.side_effect = websocket.WebSocketConnectionClosedException
        c._write_loop()
        self.assertEqual(c.state, 'disconnected')

    @mock.patch('engineio.client.original_signal_handler')
    def test_signal_handler(self, original_handler):
        clients = [mock.MagicMock(), mock.MagicMock()]
        client.connected_clients = clients[:]
        client.connected_clients[0].is_asyncio_based.return_value = False
        client.connected_clients[1].is_asyncio_based.return_value = True
        client.signal_handler('sig', 'frame')
        clients[0].disconnect.assert_called_once_with(abort=True)
        clients[1].start_background_task.assert_called_once_with(
            clients[1].disconnect, abort=True)
