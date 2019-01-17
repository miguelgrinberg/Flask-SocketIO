import sys
import time
import unittest

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
    from engineio import asyncio_socket
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
class TestSocket(unittest.TestCase):
    def _get_read_mock_coro(self, payload):
        mock_input = mock.MagicMock()
        mock_input.read = AsyncMock()
        mock_input.read.mock.return_value = payload
        return mock_input

    def _get_mock_server(self):
        mock_server = mock.Mock()
        mock_server.ping_timeout = 0.2
        mock_server.ping_interval = 0.2
        mock_server.async_handlers = False
        mock_server._async = {'asyncio': True,
                              'create_route': mock.MagicMock(),
                              'translate_request': mock.MagicMock(),
                              'make_response': mock.MagicMock(),
                              'websocket': 'w',
                              'websocket_class': 'wc'}
        mock_server._async['translate_request'].return_value = 'request'
        mock_server._async['make_response'].return_value = 'response'
        mock_server._trigger_event = AsyncMock()
        return mock_server

    def test_create(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        self.assertEqual(s.server, mock_server)
        self.assertEqual(s.sid, 'sid')
        self.assertFalse(s.upgraded)
        self.assertFalse(s.closed)
        self.assertTrue(hasattr(s.queue, 'get'))
        self.assertTrue(hasattr(s.queue, 'put'))
        self.assertTrue(hasattr(s.queue, 'task_done'))
        self.assertTrue(hasattr(s.queue, 'join'))

    def test_empty_poll(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        self.assertRaises(exceptions.QueueEmpty, _run, s.poll())

    def test_poll(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        _run(s.send(pkt1))
        _run(s.send(pkt2))
        self.assertEqual(_run(s.poll()), [pkt1, pkt2])

    def test_poll_none(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        _run(s.queue.put(None))
        self.assertEqual(_run(s.poll()), [])

    def test_ping_pong(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        _run(s.receive(packet.Packet(packet.PING, data='abc')))
        r = _run(s.poll())
        self.assertEqual(len(r), 1)
        self.assertTrue(r[0].encode(), b'3abc')

    def test_message_sync_handler(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        _run(s.receive(packet.Packet(packet.MESSAGE, data='foo')))
        mock_server._trigger_event.mock.assert_called_once_with(
            'message', 'sid', 'foo', run_async=False)

    def test_message_async_handler(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        mock_server.async_handlers = True
        _run(s.receive(packet.Packet(packet.MESSAGE, data='foo')))
        mock_server._trigger_event.mock.assert_called_once_with(
            'message', 'sid', 'foo', run_async=True)

    def test_invalid_packet(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        self.assertRaises(exceptions.UnknownPacketError, _run,
                          s.receive(packet.Packet(packet.OPEN)))

    def test_timeout(self):
        mock_server = self._get_mock_server()
        mock_server.ping_interval = -0.1
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.last_ping = time.time() - 1
        s.close = AsyncMock()
        _run(s.send('packet'))
        s.close.mock.assert_called_once_with(wait=False, abort=False)

    def test_polling_read(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'foo')
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        _run(s.send(pkt1))
        _run(s.send(pkt2))
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        packets = _run(s.handle_get_request(environ))
        self.assertEqual(packets, [pkt1, pkt2])

    def test_polling_read_error(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'foo')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        self.assertRaises(exceptions.QueueEmpty, _run,
                          s.handle_get_request(environ))

    def test_polling_write(self):
        mock_server = self._get_mock_server()
        mock_server.max_http_buffer_size = 1000
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        p = payload.Payload(packets=[pkt1, pkt2]).encode()
        s = asyncio_socket.AsyncSocket(mock_server, 'foo')
        s.receive = AsyncMock()
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo',
                   'CONTENT_LENGTH': len(p),
                   'wsgi.input': self._get_read_mock_coro(p)}
        _run(s.handle_post_request(environ))
        self.assertEqual(s.receive.mock.call_count, 2)

    def test_polling_write_too_large(self):
        mock_server = self._get_mock_server()
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        p = payload.Payload(packets=[pkt1, pkt2]).encode()
        mock_server.max_http_buffer_size = len(p) - 1
        s = asyncio_socket.AsyncSocket(mock_server, 'foo')
        s.receive = AsyncMock()
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo',
                   'CONTENT_LENGTH': len(p),
                   'wsgi.input': self._get_read_mock_coro(p)}
        self.assertRaises(exceptions.ContentTooLongError, _run,
                          s.handle_post_request(environ))

    def test_upgrade_handshake(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'foo')
        s._upgrade_websocket = AsyncMock()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'HTTP_CONNECTION': 'Foo,Upgrade,Bar',
                   'HTTP_UPGRADE': 'websocket'}
        _run(s.handle_get_request(environ))
        s._upgrade_websocket.mock.assert_called_once_with(environ)

    def test_upgrade(self):
        mock_server = self._get_mock_server()
        mock_server._async['websocket'] = mock.MagicMock()
        mock_server._async['websocket_class'] = 'WebSocket'
        mock_ws = AsyncMock()
        mock_server._async['websocket'].WebSocket.return_value = mock_ws
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        environ = "foo"
        _run(s._upgrade_websocket(environ))
        mock_server._async['websocket'].WebSocket.assert_called_once_with(
            s._websocket_handler)
        mock_ws.mock.assert_called_once_with(environ)

    def test_upgrade_twice(self):
        mock_server = self._get_mock_server()
        mock_server._async['websocket'] = mock.MagicMock()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        s.upgraded = True
        environ = "foo"
        self.assertRaises(IOError, _run, s._upgrade_websocket(environ))

    def test_upgrade_packet(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        _run(s.receive(packet.Packet(packet.UPGRADE)))
        r = _run(s.poll())
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].encode(), packet.Packet(packet.NOOP).encode())

    def test_upgrade_no_probe(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        ws = mock.MagicMock()
        ws.wait = AsyncMock()
        ws.wait.mock.return_value = packet.Packet(packet.NOOP).encode(
            always_bytes=False)
        _run(s._websocket_handler(ws))
        self.assertFalse(s.upgraded)

    def test_upgrade_no_upgrade_packet(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        s.queue.join = AsyncMock(return_value=None)
        ws = mock.MagicMock()
        ws.send = AsyncMock()
        ws.wait = AsyncMock()
        probe = six.text_type('probe')
        ws.wait.mock.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(
                always_bytes=False),
            packet.Packet(packet.NOOP).encode(always_bytes=False)]
        _run(s._websocket_handler(ws))
        ws.send.mock.assert_called_once_with(packet.Packet(
            packet.PONG, data=probe).encode(always_bytes=False))
        self.assertEqual(_run(s.queue.get()).packet_type, packet.NOOP)
        self.assertFalse(s.upgraded)

    def test_upgrade_not_supported(self):
        mock_server = self._get_mock_server()
        mock_server._async['websocket'] = None
        mock_server._async['websocket_class'] = None
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        environ = "foo"
        _run(s._upgrade_websocket(environ))
        mock_server._bad_request.assert_called_once_with()

    def test_close_packet(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        s.close = AsyncMock()
        _run(s.receive(packet.Packet(packet.CLOSE)))
        s.close.mock.assert_called_once_with(wait=False, abort=True)

    def test_websocket_read_write(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = False
        s.queue.join = AsyncMock(return_value=None)
        foo = six.text_type('foo')
        bar = six.text_type('bar')
        s.poll = AsyncMock(side_effect=[
            [packet.Packet(packet.MESSAGE, data=bar)], None])
        ws = mock.MagicMock()
        ws.send = AsyncMock()
        ws.wait = AsyncMock()
        ws.wait.mock.side_effect = [
            packet.Packet(packet.MESSAGE, data=foo).encode(
                always_bytes=False),
            None]
        _run(s._websocket_handler(ws))
        self.assertTrue(s.connected)
        self.assertTrue(s.upgraded)
        self.assertEqual(mock_server._trigger_event.mock.call_count, 2)
        mock_server._trigger_event.mock.assert_has_calls([
            mock.call('message', 'sid', 'foo', run_async=False),
            mock.call('disconnect', 'sid')])
        ws.send.mock.assert_called_with('4bar')

    def test_websocket_upgrade_read_write(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        s.queue.join = AsyncMock(return_value=None)
        foo = six.text_type('foo')
        bar = six.text_type('bar')
        probe = six.text_type('probe')
        s.poll = AsyncMock(side_effect=[
            [packet.Packet(packet.MESSAGE, data=bar)], exceptions.QueueEmpty])
        ws = mock.MagicMock()
        ws.send = AsyncMock()
        ws.wait = AsyncMock()
        ws.wait.mock.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(
                always_bytes=False),
            packet.Packet(packet.UPGRADE).encode(always_bytes=False),
            packet.Packet(packet.MESSAGE, data=foo).encode(
                always_bytes=False),
            None]
        _run(s._websocket_handler(ws))
        self.assertTrue(s.upgraded)
        self.assertEqual(mock_server._trigger_event.mock.call_count, 2)
        mock_server._trigger_event.mock.assert_has_calls([
            mock.call('message', 'sid', 'foo', run_async=False),
            mock.call('disconnect', 'sid')])
        ws.send.mock.assert_called_with('4bar')

    def test_websocket_upgrade_with_payload(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = True
        s.queue.join = AsyncMock(return_value=None)
        probe = six.text_type('probe')
        ws = mock.MagicMock()
        ws.send = AsyncMock()
        ws.wait = AsyncMock()
        ws.wait.mock.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(
                always_bytes=False),
            packet.Packet(packet.UPGRADE, data=b'2').encode(
                always_bytes=False)]
        _run(s._websocket_handler(ws))
        self.assertTrue(s.upgraded)

    def test_websocket_read_write_wait_fail(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = False
        s.queue.join = AsyncMock(return_value=None)
        foo = six.text_type('foo')
        bar = six.text_type('bar')
        s.poll = AsyncMock(side_effect=[
            [packet.Packet(packet.MESSAGE, data=bar)],
            [packet.Packet(packet.MESSAGE, data=bar)], exceptions.QueueEmpty])
        ws = mock.MagicMock()
        ws.send = AsyncMock()
        ws.wait = AsyncMock()
        ws.wait.mock.side_effect = [
            packet.Packet(packet.MESSAGE, data=foo).encode(
                always_bytes=False),
            RuntimeError]
        ws.send.mock.side_effect = [None, RuntimeError]
        _run(s._websocket_handler(ws))
        self.assertEqual(s.closed, True)

    def test_websocket_ignore_invalid_packet(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.connected = False
        s.queue.join = AsyncMock(return_value=None)
        foo = six.text_type('foo')
        bar = six.text_type('bar')
        s.poll = AsyncMock(side_effect=[
            [packet.Packet(packet.MESSAGE, data=bar)], exceptions.QueueEmpty])
        ws = mock.MagicMock()
        ws.send = AsyncMock()
        ws.wait = AsyncMock()
        ws.wait.mock.side_effect = [
            packet.Packet(packet.OPEN).encode(always_bytes=False),
            packet.Packet(packet.MESSAGE, data=foo).encode(
                always_bytes=False),
            None]
        _run(s._websocket_handler(ws))
        self.assertTrue(s.connected)
        self.assertEqual(mock_server._trigger_event.mock.call_count, 2)
        mock_server._trigger_event.mock.assert_has_calls([
            mock.call('message', 'sid', foo, run_async=False),
            mock.call('disconnect', 'sid')])
        ws.send.mock.assert_called_with('4bar')

    def test_send_after_close(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        _run(s.close(wait=False))
        self.assertRaises(exceptions.SocketIsClosedError, _run,
                          s.send(packet.Packet(packet.NOOP)))

    def test_close_after_close(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        _run(s.close(wait=False))
        self.assertTrue(s.closed)
        self.assertEqual(mock_server._trigger_event.mock.call_count, 1)
        mock_server._trigger_event.mock.assert_called_once_with('disconnect',
                                                                'sid')
        _run(s.close())
        self.assertEqual(mock_server._trigger_event.mock.call_count, 1)

    def test_close_and_wait(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.queue = mock.MagicMock()
        s.queue.put = AsyncMock()
        s.queue.join = AsyncMock()
        _run(s.close(wait=True))
        s.queue.join.mock.assert_called_once_with()

    def test_close_without_wait(self):
        mock_server = self._get_mock_server()
        s = asyncio_socket.AsyncSocket(mock_server, 'sid')
        s.queue = mock.MagicMock()
        s.queue.put = AsyncMock()
        s.queue.join = AsyncMock()
        _run(s.close(wait=False))
        self.assertEqual(s.queue.join.mock.call_count, 0)
