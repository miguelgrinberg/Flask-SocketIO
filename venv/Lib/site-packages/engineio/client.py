import logging
try:
    import queue
except ImportError:  # pragma: no cover
    import Queue as queue
import signal
import threading
import time

import six
from six.moves import urllib
try:
    import urllib3
except ImportError:  # pragma: no cover
    urllib3 = None
try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None
from . import exceptions
from . import packet
from . import payload

default_logger = logging.getLogger('engineio.client')
connected_clients = []

if six.PY2:  # pragma: no cover
    ConnectionError = OSError


def signal_handler(sig, frame):
    """SIGINT handler.

    Disconnect all active clients and then invoke the original signal handler.
    """
    for client in connected_clients[:]:
        if client.is_asyncio_based():
            client.start_background_task(client.disconnect, abort=True)
        else:
            client.disconnect(abort=True)
    return original_signal_handler(sig, frame)


original_signal_handler = signal.signal(signal.SIGINT, signal_handler)


class Client(object):
    """An Engine.IO client.

    This class implements a fully compliant Engine.IO web client with support
    for websocket and long-polling transports.

    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``. The default is
                   ``False``.
    :param json: An alternative json module to use for encoding and decoding
                 packets. Custom json modules must have ``dumps`` and ``loads``
                 functions that are compatible with the standard library
                 versions.
    """
    event_names = ['connect', 'disconnect', 'message']

    def __init__(self, logger=False, json=None):
        self.handlers = {}
        self.base_url = None
        self.transports = None
        self.current_transport = None
        self.sid = None
        self.upgrades = None
        self.ping_interval = None
        self.ping_timeout = None
        self.pong_received = True
        self.http = None
        self.ws = None
        self.read_loop_task = None
        self.write_loop_task = None
        self.ping_loop_task = None
        self.ping_loop_event = self.create_event()
        self.queue = None
        self.state = 'disconnected'

        if json is not None:
            packet.Packet.json = json
        if not isinstance(logger, bool):
            self.logger = logger
        else:
            self.logger = default_logger
            if not logging.root.handlers and \
                    self.logger.level == logging.NOTSET:
                if logger:
                    self.logger.setLevel(logging.INFO)
                else:
                    self.logger.setLevel(logging.ERROR)
                self.logger.addHandler(logging.StreamHandler())

    def is_asyncio_based(self):
        return False

    def on(self, event, handler=None):
        """Register an event handler.

        :param event: The event name. Can be ``'connect'``, ``'message'`` or
                      ``'disconnect'``.
        :param handler: The function that should be invoked to handle the
                        event. When this parameter is not given, the method
                        acts as a decorator for the handler function.

        Example usage::

            # as a decorator:
            @eio.on('connect')
            def connect_handler():
                print('Connection request')

            # as a method:
            def message_handler(msg):
                print('Received message: ', msg)
                eio.send('response')
            eio.on('message', message_handler)
        """
        if event not in self.event_names:
            raise ValueError('Invalid event')

        def set_handler(handler):
            self.handlers[event] = handler
            return handler

        if handler is None:
            return set_handler
        set_handler(handler)

    def connect(self, url, headers={}, transports=None,
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

        Example usage::

            eio = engineio.Client()
            eio.connect('http://localhost:5000')
        """
        if self.state != 'disconnected':
            raise ValueError('Client is not in a disconnected state')
        valid_transports = ['polling', 'websocket']
        if transports is not None:
            if isinstance(transports, six.string_types):
                transports = [transports]
            transports = [transport for transport in transports
                          if transport in valid_transports]
            if not transports:
                raise ValueError('No valid transports provided')
        self.transports = transports or valid_transports
        self.queue = self.create_queue()
        return getattr(self, '_connect_' + self.transports[0])(
            url, headers, engineio_path)

    def wait(self):
        """Wait until the connection with the server ends.

        Client applications can use this function to block the main thread
        during the life of the connection.
        """
        if self.read_loop_task:
            self.read_loop_task.join()

    def send(self, data, binary=None):
        """Send a message to a client.

        :param data: The data to send to the client. Data can be of type
                     ``str``, ``bytes``, ``list`` or ``dict``. If a ``list``
                     or ``dict``, the data will be serialized as JSON.
        :param binary: ``True`` to send packet as binary, ``False`` to send
                       as text. If not given, unicode (Python 2) and str
                       (Python 3) are sent as text, and str (Python 2) and
                       bytes (Python 3) are sent as binary.
        """
        self._send_packet(packet.Packet(packet.MESSAGE, data=data,
                                        binary=binary))

    def disconnect(self, abort=False):
        """Disconnect from the server.

        :param abort: If set to ``True``, do not wait for background tasks
                      associated with the connection to end.
        """
        if self.state == 'connected':
            self._send_packet(packet.Packet(packet.CLOSE))
            self.queue.put(None)
            self.state = 'disconnecting'
            self._trigger_event('disconnect', run_async=False)
            if self.current_transport == 'websocket':
                self.ws.close()
            if not abort:
                self.read_loop_task.join()
            self.state = 'disconnected'
            try:
                connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
        self._reset()

    def transport(self):
        """Return the name of the transport currently in use.

        The possible values returned by this function are ``'polling'`` and
        ``'websocket'``.
        """
        return self.current_transport

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
        """
        th = threading.Thread(target=target, args=args, kwargs=kwargs)
        th.start()
        return th

    def sleep(self, seconds=0):
        """Sleep for the requested amount of time."""
        return time.sleep(seconds)

    def create_queue(self, *args, **kwargs):
        """Create a queue object."""
        q = queue.Queue(*args, **kwargs)
        q.Empty = queue.Empty
        return q

    def create_event(self, *args, **kwargs):
        """Create an event object."""
        return threading.Event(*args, **kwargs)

    def _reset(self):
        self.state = 'disconnected'

    def _connect_polling(self, url, headers, engineio_path):
        """Establish a long-polling connection to the Engine.IO server."""
        if urllib3 is None:  # pragma: no cover
            # not installed
            self.logger.error('urllib3 is not installed -- cannot make HTTP '
                              'requests!')
            return
        self.base_url = self._get_engineio_url(url, engineio_path, 'polling')
        self.logger.info('Attempting polling connection to ' + self.base_url)
        r = self._send_request(
            'GET', self.base_url + self._get_url_timestamp(), headers=headers)
        if r is None:
            self._reset()
            raise exceptions.ConnectionError(
                'Connection refused by the server')
        if r.status != 200:
            raise exceptions.ConnectionError(
                'Unexpected status code %s in server response', r.status)
        try:
            p = payload.Payload(encoded_payload=r.data)
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
        connected_clients.append(self)
        self._trigger_event('connect', run_async=False)

        for pkt in p.packets[1:]:
            self._receive_packet(pkt)

        if 'websocket' in self.upgrades and 'websocket' in self.transports:
            # attempt to upgrade to websocket
            if self._connect_websocket(url, headers, engineio_path):
                # upgrade to websocket succeeded, we're done here
                return

        # start background tasks associated with this client
        self.ping_loop_task = self.start_background_task(self._ping_loop)
        self.write_loop_task = self.start_background_task(self._write_loop)
        self.read_loop_task = self.start_background_task(
            self._read_loop_polling)

    def _connect_websocket(self, url, headers, engineio_path):
        """Establish or upgrade to a WebSocket connection with the server."""
        if websocket is None:  # pragma: no cover
            # not installed
            self.logger.warning('websocket-client package not installed, only '
                                'polling transport is available')
            return False
        websocket_url = self._get_engineio_url(url, engineio_path, 'websocket')
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
            ws = websocket.create_connection(
                websocket_url + self._get_url_timestamp(), header=headers)
        except ConnectionError:
            if upgrade:
                self.logger.warning(
                    'WebSocket upgrade failed: connection error')
                return False
            else:
                raise exceptions.ConnectionError('Connection error')
        if upgrade:
            ws.send(packet.Packet(packet.PING, data='probe').encode())
            pkt = packet.Packet(encoded_packet=ws.recv())
            if pkt.packet_type != packet.PONG or pkt.data != 'probe':
                self.logger.warning(
                    'WebSocket upgrade failed: no PONG packet')
                return False
            ws.send(packet.Packet(packet.UPGRADE).encode())
            self.current_transport = 'websocket'
            self.logger.info('WebSocket upgrade was successful')
        else:
            open_packet = packet.Packet(encoded_packet=ws.recv())
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
            connected_clients.append(self)
            self._trigger_event('connect', run_async=False)
        self.ws = ws

        # start background tasks associated with this client
        self.ping_loop_task = self.start_background_task(self._ping_loop)
        self.write_loop_task = self.start_background_task(self._write_loop)
        self.read_loop_task = self.start_background_task(
            self._read_loop_websocket)
        return True

    def _receive_packet(self, pkt):
        """Handle incoming packets from the server."""
        packet_name = packet.packet_names[pkt.packet_type] \
            if pkt.packet_type < len(packet.packet_names) else 'UNKNOWN'
        self.logger.info(
            'Received packet %s data %s', packet_name,
            pkt.data if not isinstance(pkt.data, bytes) else '<binary>')
        if pkt.packet_type == packet.MESSAGE:
            self._trigger_event('message', pkt.data, run_async=True)
        elif pkt.packet_type == packet.PONG:
            self.pong_received = True
        elif pkt.packet_type == packet.NOOP:
            pass
        else:
            self.logger.error('Received unexpected packet of type %s',
                              pkt.packet_type)

    def _send_packet(self, pkt):
        """Queue a packet to be sent to the server."""
        if self.state != 'connected':
            return
        self.queue.put(pkt)
        self.logger.info(
            'Sending packet %s data %s',
            packet.packet_names[pkt.packet_type],
            pkt.data if not isinstance(pkt.data, bytes) else '<binary>')

    def _send_request(
            self, method, url, headers=None, body=None):  # pragma: no cover
        if self.http is None:
            self.http = urllib3.PoolManager()
        try:
            return self.http.request(method, url, headers=headers, body=body)
        except urllib3.exceptions.MaxRetryError:
            pass

    def _trigger_event(self, event, *args, **kwargs):
        """Invoke an event handler."""
        run_async = kwargs.pop('run_async', False)
        if event in self.handlers:
            if run_async:
                return self.start_background_task(self.handlers[event], *args)
            else:
                try:
                    return self.handlers[event](*args)
                except:
                    self.logger.exception(event + ' handler error')

    def _get_engineio_url(self, url, engineio_path, transport):
        """Generate the Engine.IO connection URL."""
        engineio_path = engineio_path.strip('/')
        parsed_url = urllib.parse.urlparse(url)

        if transport == 'polling':
            scheme = 'http'
        elif transport == 'websocket':
            scheme = 'ws'
        else:  # pragma: no cover
            raise ValueError('invalid transport')
        if parsed_url.scheme in ['https', 'wss']:
            scheme += 's'

        return ('{scheme}://{netloc}/{path}/?{query}'
                '{sep}transport={transport}&EIO=3').format(
                    scheme=scheme, netloc=parsed_url.netloc,
                    path=engineio_path, query=parsed_url.query,
                    sep='&' if parsed_url.query else '',
                    transport=transport)

    def _get_url_timestamp(self):
        """Generate the Engine.IO query string timestamp."""
        return '&t=' + str(time.time())

    def _ping_loop(self):
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
                    self.ws.close()
                self.queue.put(None)
                self._reset()
                break
            self.pong_received = False
            self._send_packet(packet.Packet(packet.PING))
            self.ping_loop_event.wait(timeout=self.ping_interval)
        self.logger.info('Exiting ping task')

    def _read_loop_polling(self):
        """Read packets by polling the Engine.IO server."""
        while self.state == 'connected':
            self.logger.info(
                'Sending polling GET request to ' + self.base_url)
            r = self._send_request(
                'GET', self.base_url + self._get_url_timestamp())
            if r is None:
                self.logger.warning(
                    'Connection refused by the server, aborting')
                self.queue.put(None)
                break
            if r.status != 200:
                self.logger.warning('Unexpected status code %s in server '
                                    'response, aborting', r.status)
                self.queue.put(None)
                break
            try:
                p = payload.Payload(encoded_payload=r.data)
            except ValueError:
                self.logger.warning(
                    'Unexpected packet from server, aborting')
                self.queue.put(None)
                break
            for pkt in p.packets:
                self._receive_packet(pkt)

        self.logger.info('Waiting for write loop task to end')
        self.write_loop_task.join()
        self.logger.info('Waiting for ping loop task to end')
        self.ping_loop_event.set()
        self.ping_loop_task.join()
        if self.state == 'connected':
            self._trigger_event('disconnect', run_async=False)
            try:
                connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
            self._reset()
        self.logger.info('Exiting read loop task')

    def _read_loop_websocket(self):
        """Read packets from the Engine.IO WebSocket connection."""
        while self.state == 'connected':
            p = None
            try:
                p = self.ws.recv()
            except websocket.WebSocketConnectionClosedException:
                self.logger.warning(
                    'WebSocket connection was closed, aborting')
                self.queue.put(None)
                break
            except Exception as e:
                self.logger.info(
                    'Unexpected error "%s", aborting', str(e))
                self.queue.put(None)
                break
            if isinstance(p, six.text_type):  # pragma: no cover
                p = p.encode('utf-8')
            pkt = packet.Packet(encoded_packet=p)
            self._receive_packet(pkt)

        self.logger.info('Waiting for write loop task to end')
        self.write_loop_task.join()
        self.logger.info('Waiting for ping loop task to end')
        self.ping_loop_event.set()
        self.ping_loop_task.join()
        if self.state == 'connected':
            self._trigger_event('disconnect', run_async=False)
            try:
                connected_clients.remove(self)
            except ValueError:  # pragma: no cover
                pass
            self._reset()
        self.logger.info('Exiting read loop task')

    def _write_loop(self):
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
                packets = [self.queue.get(timeout=timeout)]
            except self.queue.Empty:
                self.logger.error('packet queue is empty, aborting')
                self._reset()
                break
            if packets == [None]:
                self.queue.task_done()
                packets = []
            else:
                while True:
                    try:
                        packets.append(self.queue.get(block=False))
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
                r = self._send_request(
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
                        self.ws.send(pkt.encode())
                        self.queue.task_done()
                except websocket.WebSocketConnectionClosedException:
                    self.logger.warning(
                        'WebSocket connection was closed, aborting')
                    self._reset()
                    break
        self.logger.info('Exiting write loop task')
