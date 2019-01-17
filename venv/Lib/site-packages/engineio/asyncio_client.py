import asyncio

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None
import six
try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None

from . import client
from . import exceptions
from . import packet
from . import payload


class AsyncClient(client.Client):
    """An Engine.IO client for asyncio.

    This class implements a fully compliant Engine.IO web client with support
    for websocket and long-polling transports, compatible with the asyncio
    framework on Python 3.5 or newer.

    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``. The default is
                   ``False``.
    :param json: An alternative json module to use for encoding and decoding
                 packets. Custom json modules must have ``dumps`` and ``loads``
                 functions that are compatible with the standard library
                 versions.
    """
    def is_asyncio_based(self):
        return True

    async def connect(self, url, headers={}, transports=None,
                      engineio_path='engine.io'):
        """Connect to an Engine.IO server.

        :param url: The URL of the Engine.IO server. It can include custom
                    query string parameters if required by the server.
        :param headers: A dictionary with custom headers to send with the
                        connection request.
        :param transports: The list of allowed transports. Valid transports
                           are ``'polling'`` and ``'websocket'``. If not
                           given, the polling transport is connected first,
                           then an upgrade to websocket is attempted.
        :param engineio_path: The endpoint where the Engine.IO server is
                              installed. The default value is appropriate for
                              most cases.

        Note: this method is a coroutine.

        Example usage::

            eio = engineio.Client()
            await eio.connect('http://localhost:5000')
        """
        if self.state != 'disconnected':
            raise ValueError('Client is not in a disconnected state')
        valid_transports = ['polling', 'websocket']
        if transports is not None:
            if isinstance(transports, six.text_type):
                transports = [transports]
            transports = [transport for transport in transports
                          if transport in valid_transports]
            if not transports:
                raise ValueError('No valid transports provided')
        self.transports = transports or valid_transports
        self.queue = self.create_queue()
        return await getattr(self, '_connect_' + self.transports[0])(
            url, headers, engineio_path)

    async def wait(self):
        """Wait until the connection with the server ends.

        Client applications can use this function to block the main thread
        during the life of the connection.

        Note: this method is a coroutine.
        """
        if self.read_loop_task:
            await self.read_loop_task

    async def send(self, data, binary=None):
        """Send a message to a client.

        :param data: The data to send to the client. Data can be of type
                     ``str``, ``bytes``, ``list`` or ``dict``. If a ``list``
                     or ``dict``, the data will be serialized as JSON.
        :param binary: ``True`` to send packet as binary, ``False`` to send
                       as text. If not given, unicode (Python 2) and str
                       (Python 3) are sent as text, and str (Python 2) and
                       bytes (Python 3) are sent as binary.

        Note: this method is a coroutine.
        """
        await self._send_packet(packet.Packet(packet.MESSAGE, data=data,
                                              binary=binary))

    async def disconnect(self, abort=False):
        """Disconnect from the server.

        :param abort: If set to ``True``, do not wait for background tasks
                      associated with the connection to end.

        Note: this method is a coroutine.
        """
        if self.state == 'connected':
            await self._send_packet(packet.Packet(packet.CLOSE))
            await self.queue.put(None)
            self.state = 'disconnecting'
            await self._trigger_event('disconnect', run_async=False)
            if self.current_transport == 'websocket':
                await self.ws.close()
            if not abort:
                await self.read_loop_task
            self.state = 'disconnected'
            try:
                client.connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
        self._reset()

    def start_background_task(self, target, *args, **kwargs):
        """Start a background task.

        This is a utility function that applications can use to start a
        background task.

        :param target: the target function to execute.
        :param args: arguments to pass to the function.
        :param kwargs: keyword arguments to pass to the function.

        This function returns an object compatible with the `Thread` class in
        the Python standard library. The `start()` method on this object is
        already called by this function.

        Note: this method is a coroutine.
        """
        return asyncio.ensure_future(target(*args, **kwargs))

    async def sleep(self, seconds=0):
        """Sleep for the requested amount of time.

        Note: this method is a coroutine.
        """
        return await asyncio.sleep(seconds)

    def create_queue(self):
        """Create a queue object."""
        q = asyncio.Queue()
        q.Empty = asyncio.QueueEmpty
        return q

    def create_event(self):
        """Create an event object."""
        return asyncio.Event()

    async def _connect_polling(self, url, headers, engineio_path):
        """Establish a long-polling connection to the Engine.IO server."""
        if aiohttp is None:  # pragma: no cover
            self.logger.error('aiohttp not installed -- cannot make HTTP '
                              'requests!')
            return
        self.base_url = self._get_engineio_url(url, engineio_path, 'polling')
        self.logger.info('Attempting polling connection to ' + self.base_url)
        r = await self._send_request(
            'GET', self.base_url + self._get_url_timestamp(), headers=headers)
        if r is None:
            self._reset()
            raise exceptions.ConnectionError(
                'Connection refused by the server')
        if r.status != 200:
            raise exceptions.ConnectionError(
                'Unexpected status code %s in server response', r.status)
        try:
            p = payload.Payload(encoded_payload=await r.read())
        except ValueError:
            six.raise_from(exceptions.ConnectionError(
                'Unexpected response from server'), None)
        open_packet = p.packets[0]
        if open_packet.packet_type != packet.OPEN:
            raise exceptions.ConnectionError(
                'OPEN packet not returned by server')
        self.logger.info(
            'Polling connection accepted with ' + str(open_packet.data))
        self.sid = open_packet.data['sid']
        self.upgrades = open_packet.data['upgrades']
        self.ping_interval = open_packet.data['pingInterval'] / 1000.0
        self.ping_timeout = open_packet.data['pingTimeout'] / 1000.0
        self.current_transport = 'polling'
        self.base_url += '&sid=' + self.sid

        self.state = 'connected'
        client.connected_clients.append(self)
        await self._trigger_event('connect', run_async=False)

        for pkt in p.packets[1:]:
            await self._receive_packet(pkt)

        if 'websocket' in self.upgrades and 'websocket' in self.transports:
            # attempt to upgrade to websocket
            if await self._connect_websocket(url, headers, engineio_path):
                # upgrade to websocket succeeded, we're done here
                return

        self.ping_loop_task = self.start_background_task(self._ping_loop)
        self.write_loop_task = self.start_background_task(self._write_loop)
        self.read_loop_task = self.start_background_task(
            self._read_loop_polling)

    async def _connect_websocket(self, url, headers, engineio_path):
        """Establish or upgrade to a WebSocket connection with the server."""
        if websockets is None:  # pragma: no cover
            self.logger.error('websockets package not installed')
            return False
        websocket_url = self._get_engineio_url(url, engineio_path,
                                               'websocket')
        if self.sid:
            self.logger.info(
                'Attempting WebSocket upgrade to ' + websocket_url)
            upgrade = True
            websocket_url += '&sid=' + self.sid
        else:
            upgrade = False
            self.base_url = websocket_url
            self.logger.info(
                'Attempting WebSocket connection to ' + websocket_url)
        try:
            ws = await websockets.connect(
                websocket_url + self._get_url_timestamp(),
                extra_headers=headers)
        except (websockets.exceptions.InvalidURI,
                websockets.exceptions.InvalidHandshake):
            if upgrade:
                self.logger.warning(
                    'WebSocket upgrade failed: connection error')
                return False
            else:
                raise exceptions.ConnectionError('Connection error')
        if upgrade:
            await ws.send(packet.Packet(packet.PING, data='probe').encode(
                always_bytes=False))
            pkt = packet.Packet(encoded_packet=await ws.recv())
            if pkt.packet_type != packet.PONG or pkt.data != 'probe':
                self.logger.warning(
                    'WebSocket upgrade failed: no PONG packet')
                return False
            await ws.send(packet.Packet(packet.UPGRADE).encode(
                always_bytes=False))
            self.current_transport = 'websocket'
            if self.http:  # pragma: no cover
                await self.http.close()
            self.logger.info('WebSocket upgrade was successful')
        else:
            open_packet = packet.Packet(encoded_packet=await ws.recv())
            if open_packet.packet_type != packet.OPEN:
                raise exceptions.ConnectionError('no OPEN packet')
            self.logger.info(
                'WebSocket connection accepted with ' + str(open_packet.data))
            self.sid = open_packet.data['sid']
            self.upgrades = open_packet.data['upgrades']
            self.ping_interval = open_packet.data['pingInterval'] / 1000.0
            self.ping_timeout = open_packet.data['pingTimeout'] / 1000.0
            self.current_transport = 'websocket'

            self.state = 'connected'
            client.connected_clients.append(self)
            await self._trigger_event('connect', run_async=False)

        self.ws = ws
        self.ping_loop_task = self.start_background_task(self._ping_loop)
        self.write_loop_task = self.start_background_task(self._write_loop)
        self.read_loop_task = self.start_background_task(
            self._read_loop_websocket)
        return True

    async def _receive_packet(self, pkt):
        """Handle incoming packets from the server."""
        packet_name = packet.packet_names[pkt.packet_type] \
            if pkt.packet_type < len(packet.packet_names) else 'UNKNOWN'
        self.logger.info(
            'Received packet %s data %s', packet_name,
            pkt.data if not isinstance(pkt.data, bytes) else '<binary>')
        if pkt.packet_type == packet.MESSAGE:
            await self._trigger_event('message', pkt.data, run_async=True)
        elif pkt.packet_type == packet.PONG:
            self.pong_received = True
        elif pkt.packet_type == packet.NOOP:
            pass
        else:
            self.logger.error('Received unexpected packet of type %s',
                              pkt.packet_type)

    async def _send_packet(self, pkt):
        """Queue a packet to be sent to the server."""
        if self.state != 'connected':
            return
        await self.queue.put(pkt)
        self.logger.info(
            'Sending packet %s data %s',
            packet.packet_names[pkt.packet_type],
            pkt.data if not isinstance(pkt.data, bytes) else '<binary>')

    async def _send_request(
            self, method, url, headers=None, body=None):  # pragma: no cover
        if self.http is None:
            self.http = aiohttp.ClientSession()
        method = getattr(self.http, method.lower())
        try:
            return await method(url, headers=headers, data=body)
        except aiohttp.ClientError:
            return

    async def _trigger_event(self, event, *args, **kwargs):
        """Invoke an event handler."""
        run_async = kwargs.pop('run_async', False)
        ret = None
        if event in self.handlers:
            if asyncio.iscoroutinefunction(self.handlers[event]) is True:
                if run_async:
                    return self.start_background_task(self.handlers[event],
                                                      *args)
                else:
                    try:
                        ret = await self.handlers[event](*args)
                    except asyncio.CancelledError:  # pragma: no cover
                        pass
                    except:
                        self.logger.exception(event + ' async handler error')
                        if event == 'connect':
                            # if connect handler raised error we reject the
                            # connection
                            return False
            else:
                if run_async:
                    async def async_handler():
                        return self.handlers[event](*args)

                    return self.start_background_task(async_handler)
                else:
                    try:
                        ret = self.handlers[event](*args)
                    except:
                        self.logger.exception(event + ' handler error')
                        if event == 'connect':
                            # if connect handler raised error we reject the
                            # connection
                            return False
        return ret

    async def _ping_loop(self):
        """This background task sends a PING to the server at the requested
        interval.
        """
        self.pong_received = True
        self.ping_loop_event.clear()
        while self.state == 'connected':
            if not self.pong_received:
                self.logger.warning(
                    'PONG response has not been received, aborting')
                if self.ws:
                    await self.ws.close()
                await self.queue.put(None)
                self._reset()
                break
            self.pong_received = False
            await self._send_packet(packet.Packet(packet.PING))
            try:
                await asyncio.wait_for(self.ping_loop_event.wait(),
                                       self.ping_interval)
            except (asyncio.TimeoutError,
                    asyncio.CancelledError):  # pragma: no cover
                pass
        self.logger.info('Exiting ping task')

    async def _read_loop_polling(self):
        """Read packets by polling the Engine.IO server."""
        while self.state == 'connected':
            self.logger.info(
                'Sending polling GET request to ' + self.base_url)
            r = await self._send_request(
                'GET', self.base_url + self._get_url_timestamp())
            if r is None:
                self.logger.warning(
                    'Connection refused by the server, aborting')
                await self.queue.put(None)
                break
            if r.status != 200:
                self.logger.warning('Unexpected status code %s in server '
                                    'response, aborting', r.status)
                await self.queue.put(None)
                break
            try:
                p = payload.Payload(encoded_payload=await r.read())
            except ValueError:
                self.logger.warning(
                    'Unexpected packet from server, aborting')
                await self.queue.put(None)
                break
            for pkt in p.packets:
                await self._receive_packet(pkt)

        self.logger.info('Waiting for write loop task to end')
        await self.write_loop_task
        self.logger.info('Waiting for ping loop task to end')
        self.ping_loop_event.set()
        await self.ping_loop_task
        if self.state == 'connected':
            await self._trigger_event('disconnect', run_async=False)
            try:
                client.connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
            self._reset()
        self.logger.info('Exiting read loop task')

    async def _read_loop_websocket(self):
        """Read packets from the Engine.IO WebSocket connection."""
        while self.state == 'connected':
            p = None
            try:
                p = await self.ws.recv()
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(
                    'Read loop: WebSocket connection was closed, aborting')
                await self.queue.put(None)
                break
            except Exception as e:
                self.logger.info(
                    'Unexpected error "%s", aborting', str(e))
                await self.queue.put(None)
                break
            if isinstance(p, six.text_type):  # pragma: no cover
                p = p.encode('utf-8')
            pkt = packet.Packet(encoded_packet=p)
            await self._receive_packet(pkt)

        self.logger.info('Waiting for write loop task to end')
        await self.write_loop_task
        self.logger.info('Waiting for ping loop task to end')
        self.ping_loop_event.set()
        await self.ping_loop_task
        if self.state == 'connected':
            await self._trigger_event('disconnect', run_async=False)
            try:
                client.connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
            self._reset()
        self.logger.info('Exiting read loop task')

    async def _write_loop(self):
        """This background task sends packages to the server as they are
        pushed to the send queue.
        """
        while self.state == 'connected':
            # to simplify the timeout handling, use the maximum of the
            # ping interval and ping timeout as timeout, with an extra 5
            # seconds grace period
            timeout = max(self.ping_interval, self.ping_timeout) + 5
            packets = None
            try:
                packets = [await asyncio.wait_for(self.queue.get(), timeout)]
            except (self.queue.Empty, asyncio.TimeoutError,
                    asyncio.CancelledError):
                self.logger.error('packet queue is empty, aborting')
                self._reset()
                break
            if packets == [None]:
                self.queue.task_done()
                packets = []
            else:
                while True:
                    try:
                        packets.append(self.queue.get_nowait())
                    except self.queue.Empty:
                        break
                    if packets[-1] is None:
                        packets = packets[:-1]
                        self.queue.task_done()
                        break
            if not packets:
                # empty packet list returned -> connection closed
                break
            if self.current_transport == 'polling':
                p = payload.Payload(packets=packets)
                r = await self._send_request(
                    'POST', self.base_url, body=p.encode(),
                    headers={'Content-Type': 'application/octet-stream'})
                for pkt in packets:
                    self.queue.task_done()
                if r is None:
                    self.logger.warning(
                        'Connection refused by the server, aborting')
                    self._reset()
                    break
                if r.status != 200:
                    self.logger.warning('Unexpected status code %s in server '
                                        'response, aborting', r.status)
                    self._reset()
                    break
            else:
                # websocket
                try:
                    for pkt in packets:
                        await self.ws.send(pkt.encode(always_bytes=False))
                        self.queue.task_done()
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning(
                        'Write loop: WebSocket connection was closed, '
                        'aborting')
                    self._reset()
                    break
        self.logger.info('Exiting write loop task')
