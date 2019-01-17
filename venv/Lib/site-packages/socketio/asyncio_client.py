import asyncio
import logging
import random

import engineio
import six

from . import client
from . import exceptions
from . import packet

default_logger = logging.getLogger('socketio.client')


class AsyncClient(client.Client):
    """A Socket.IO client for asyncio.

    This class implements a fully compliant Socket.IO web client with support
    for websocket and long-polling transports.

    :param reconnection: ``True`` if the client should automatically attempt to
                         reconnect to the server after an interruption, or
                         ``False`` to not reconnect. The default is ``True``.
    :param reconnection_attempts: How many reconnection attempts to issue
                                  before giving up, or 0 for infinity attempts.
                                  The default is 0.
    :param reconnection_delay: How long to wait in seconds before the first
                               reconnection attempt. Each successive attempt
                               doubles this delay.
    :param reconnection_delay_max: The maximum delay between reconnection
                                   attempts.
    :param randomization_factor: Randomization amount for each delay between
                                 reconnection attempts. The default is 0.5,
                                 which means that each delay is randomly
                                 adjusted by +/- 50%.
    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``. The default is
                   ``False``.
    :param binary: ``True`` to support binary payloads, ``False`` to treat all
                   payloads as text. On Python 2, if this is set to ``True``,
                   ``unicode`` values are treated as text, and ``str`` and
                   ``bytes`` values are treated as binary.  This option has no
                   effect on Python 3, where text and binary payloads are
                   always automatically discovered.
    :param json: An alternative json module to use for encoding and decoding
                 packets. Custom json modules must have ``dumps`` and ``loads``
                 functions that are compatible with the standard library
                 versions.

    The Engine.IO configuration supports the following settings:

    :param engineio_logger: To enable Engine.IO logging set to ``True`` or pass
                            a logger object to use. To disable logging set to
                            ``False``. The default is ``False``.
    """
    def is_asyncio_based(self):
        return True

    async def connect(self, url, headers={}, transports=None,
                      namespaces=None, socketio_path='socket.io'):
        """Connect to a Socket.IO server.

        :param url: The URL of the Socket.IO server. It can include custom
                    query string parameters if required by the server.
        :param headers: A dictionary with custom headers to send with the
                        connection request.
        :param transports: The list of allowed transports. Valid transports
                           are ``'polling'`` and ``'websocket'``. If not
                           given, the polling transport is connected first,
                           then an upgrade to websocket is attempted.
        :param namespaces: The list of custom namespaces to connect, in
                           addition to the default namespace. If not given,
                           the namespace list is obtained from the registered
                           event handlers.
        :param socketio_path: The endpoint where the Socket.IO server is
                              installed. The default value is appropriate for
                              most cases.

        Note: this method is a coroutine.

        Example usage::

            sio = socketio.Client()
            sio.connect('http://localhost:5000')
        """
        self.connection_url = url
        self.connection_headers = headers
        self.connection_transports = transports
        self.connection_namespaces = namespaces
        self.socketio_path = socketio_path

        if namespaces is None:
            namespaces = set(self.handlers.keys()).union(
                set(self.namespace_handlers.keys()))
        elif isinstance(namespaces, six.string_types):
            namespaces = [namespaces]
            self.connection_namespaces = namespaces
        self.namespaces = [n for n in namespaces if n != '/']
        try:
            await self.eio.connect(url, headers=headers,
                                   transports=transports,
                                   engineio_path=socketio_path)
        except engineio.exceptions.ConnectionError as exc:
            six.raise_from(exceptions.ConnectionError(exc.args[0]), None)

    async def wait(self):
        """Wait until the connection with the server ends.

        Client applications can use this function to block the main thread
        during the life of the connection.

        Note: this method is a coroutine.
        """
        while True:
            await self.eio.wait()
            await self.sleep(1)  # give the reconnect task time to start up
            if not self._reconnect_task:
                break
            await self._reconnect_task
            if self.eio.state != 'connected':
                break

    async def emit(self, event, data=None, namespace=None, callback=None,
                   wait=False, timeout=60):
        """Emit a custom event to one or more connected clients.

        :param event: The event name. It can be any string. The event names
                      ``'connect'``, ``'message'`` and ``'disconnect'`` are
                      reserved and should not be used.
        :param data: The data to send to the client or clients. Data can be of
                     type ``str``, ``bytes``, ``list`` or ``dict``. If a
                     ``list`` or ``dict``, the data will be serialized as JSON.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the event is emitted to the
                          default namespace.
        :param callback: If given, this function will be called to acknowledge
                         the the client has received the message. The arguments
                         that will be passed to the function are those provided
                         by the client. Callback functions can only be used
                         when addressing an individual client.
        :param wait: If set to ``True``, this function will wait for the
                     server to handle the event and acknowledge it via its
                     callback function. The value(s) passed by the server to
                     its callback will be returned. If set to ``False``,
                     this function emits the event and returns immediately.
        :param timeout: If ``wait`` is set to ``True``, this parameter
                        specifies a waiting timeout. If the timeout is reached
                        before the server acknowledges the event, then a
                        ``TimeoutError`` exception is raised.

        Note: this method is a coroutine.
        """
        namespace = namespace or '/'
        self.logger.info('Emitting event "%s" [%s]', event, namespace)
        if wait is True:
            callback_event = self.eio.create_event()
            callback_args = []

            def event_callback(*args):
                callback_args.append(args)
                callback_event.set()

            callback = event_callback

        if callback is not None:
            id = self._generate_ack_id(namespace, callback)
        else:
            id = None
        if six.PY2 and not self.binary:
            binary = False  # pragma: nocover
        else:
            binary = None
        # tuples are expanded to multiple arguments, everything else is sent
        # as a single argument
        if isinstance(data, tuple):
            data = list(data)
        elif data is not None:
            data = [data]
        else:
            data = []
        await self._send_packet(packet.Packet(
            packet.EVENT, namespace=namespace, data=[event] + data, id=id,
            binary=binary))
        if wait is True:
            try:
                await asyncio.wait_for(callback_event.wait(), timeout)
            except asyncio.TimeoutError:
                six,raise_from(exceptions.TimeoutError(), None)
            return callback_args[0] if len(callback_args[0]) > 1 \
                else callback_args[0][0] if len(callback_args[0]) == 1 \
                    else None

    async def send(self, data, namespace=None, callback=None, wait=False,
                   timeout=60):
        """Send a message to one or more connected clients.

        This function emits an event with the name ``'message'``. Use
        :func:`emit` to issue custom event names.

        :param data: The data to send to the client or clients. Data can be of
                     type ``str``, ``bytes``, ``list`` or ``dict``. If a
                     ``list`` or ``dict``, the data will be serialized as JSON.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the event is emitted to the
                          default namespace.
        :param callback: If given, this function will be called to acknowledge
                         the the client has received the message. The arguments
                         that will be passed to the function are those provided
                         by the client. Callback functions can only be used
                         when addressing an individual client.
        :param wait: If set to ``True``, this function will wait for the
                     server to handle the event and acknowledge it via its
                     callback function. The value(s) passed by the server to
                     its callback will be returned. If set to ``False``,
                     this function emits the event and returns immediately.
        :param timeout: If ``wait`` is set to ``True``, this parameter
                        specifies a waiting timeout. If the timeout is reached
                        before the server acknowledges the event, then a
                        ``TimeoutError`` exception is raised.

        Note: this method is a coroutine.
        """
        await self.emit('message', data=data, namespace=namespace,
                        callback=callback, wait=wait, timeout=timeout)

    async def disconnect(self):
        """Disconnect from the server.

        Note: this method is a coroutine.
        """
        for n in self.namespaces:
            await self._trigger_event('disconnect', namespace=n)
            await self._send_packet(packet.Packet(packet.DISCONNECT,
                                    namespace=n))
        await self._trigger_event('disconnect', namespace='/')
        await self._send_packet(packet.Packet(
            packet.DISCONNECT, namespace='/'))
        await self.eio.disconnect(abort=True)

    def start_background_task(self, target, *args, **kwargs):
        """Start a background task using the appropriate async model.

        This is a utility function that applications can use to start a
        background task using the method that is compatible with the
        selected async mode.

        :param target: the target function to execute.
        :param args: arguments to pass to the function.
        :param kwargs: keyword arguments to pass to the function.

        This function returns an object compatible with the `Thread` class in
        the Python standard library. The `start()` method on this object is
        already called by this function.
        """
        return self.eio.start_background_task(target, *args, **kwargs)

    async def sleep(self, seconds=0):
        """Sleep for the requested amount of time using the appropriate async
        model.

        This is a utility function that applications can use to put a task to
        sleep without having to worry about using the correct call for the
        selected async mode.

        Note: this method is a coroutine.
        """
        return await self.eio.sleep(seconds)

    async def _send_packet(self, pkt):
        """Send a Socket.IO packet to the server."""
        encoded_packet = pkt.encode()
        if isinstance(encoded_packet, list):
            binary = False
            for ep in encoded_packet:
                await self.eio.send(ep, binary=binary)
                binary = True
        else:
            await self.eio.send(encoded_packet, binary=False)

    async def _handle_connect(self, namespace):
        namespace = namespace or '/'
        self.logger.info('Namespace {} is connected'.format(namespace))
        await self._trigger_event('connect', namespace=namespace)
        if namespace == '/':
            for n in self.namespaces:
                await self._send_packet(packet.Packet(packet.CONNECT,
                                        namespace=n))
        elif namespace not in self.namespaces:
            self.namespaces.append(namespace)

    async def _handle_disconnect(self, namespace):
        namespace = namespace or '/'
        await self._trigger_event('disconnect', namespace=namespace)
        if namespace in self.namespaces:
            self.namespaces.remove(namespace)

    async def _handle_event(self, namespace, id, data):
        namespace = namespace or '/'
        self.logger.info('Received event "%s" [%s]', data[0], namespace)
        r = await self._trigger_event(data[0], namespace, *data[1:])
        if id is not None:
            # send ACK packet with the response returned by the handler
            # tuples are expanded as multiple arguments
            if r is None:
                data = []
            elif isinstance(r, tuple):
                data = list(r)
            else:
                data = [r]
            if six.PY2 and not self.binary:
                binary = False  # pragma: nocover
            else:
                binary = None
            await self._send_packet(packet.Packet(
                packet.ACK, namespace=namespace, id=id, data=data,
                binary=binary))

    async def _handle_ack(self, namespace, id, data):
        namespace = namespace or '/'
        self.logger.info('Received ack [%s]', namespace)
        callback = None
        try:
            callback = self.callbacks[namespace][id]
        except KeyError:
            # if we get an unknown callback we just ignore it
            self.logger.warning('Unknown callback received, ignoring.')
        else:
            del self.callbacks[namespace][id]
        if callback is not None:
            if asyncio.iscoroutinefunction(callback):
                await callback(*data)
            else:
                callback(*data)

    def _handle_error(self, namespace):
        namespace = namespace or '/'
        self.logger.info('Connection to namespace {} was rejected'.format(
            namespace))
        if namespace in self.namespaces:
            self.namespaces.remove(namespace)

    async def _trigger_event(self, event, namespace, *args):
        """Invoke an application event handler."""
        # first see if we have an explicit handler for the event
        if namespace in self.handlers and event in self.handlers[namespace]:
            if asyncio.iscoroutinefunction(self.handlers[namespace][event]):
                try:
                    ret = await self.handlers[namespace][event](*args)
                except asyncio.CancelledError:  # pragma: no cover
                    ret = None
            else:
                ret = self.handlers[namespace][event](*args)
            return ret

        # or else, forward the event to a namepsace handler if one exists
        elif namespace in self.namespace_handlers:
            return await self.namespace_handlers[namespace].trigger_event(
                event, *args)

    async def _handle_reconnect(self):
        attempt_count = 0
        current_delay = self.reconnection_delay
        while True:
            delay = current_delay
            current_delay *= 2
            if delay > self.reconnection_delay_max:
                delay = self.reconnection_delay_max
            delay += self.randomization_factor * (2 * random.random() - 1)
            self.logger.info(
                'Connection failed, new attempt in {:.02f} seconds'.format(
                    delay))
            await self.sleep(delay)
            attempt_count += 1
            try:
                await self.connect(self.connection_url,
                                   headers=self.connection_headers,
                                   transports=self.connection_transports,
                                   socketio_path=self.socketio_path)
            except (exceptions.ConnectionError, ValueError):
                pass
            else:
                self.logger.info('Reconnection successful')
                self._reconnect_task = None
                break
            if self.reconnection_attempts and \
                    attempt_count >= self.reconnection_attempts:
                self.logger.info(
                    'Maximum reconnection attempts reached, giving up')
                break

    def _handle_eio_connect(self):  # pragma: no cover
        """Handle the Engine.IO connection event."""
        self.logger.info('Engine.IO connection established')

    async def _handle_eio_message(self, data):
        """Dispatch Engine.IO messages."""
        if self._binary_packet:
            pkt = self._binary_packet
            if pkt.add_attachment(data):
                self._binary_packet = None
                if pkt.packet_type == packet.BINARY_EVENT:
                    await self._handle_event(pkt.namespace, pkt.id, pkt.data)
                else:
                    await self._handle_ack(pkt.namespace, pkt.id, pkt.data)
        else:
            pkt = packet.Packet(encoded_packet=data)
            if pkt.packet_type == packet.CONNECT:
                await self._handle_connect(pkt.namespace)
            elif pkt.packet_type == packet.DISCONNECT:
                await self._handle_disconnect(pkt.namespace)
            elif pkt.packet_type == packet.EVENT:
                await self._handle_event(pkt.namespace, pkt.id, pkt.data)
            elif pkt.packet_type == packet.ACK:
                await self._handle_ack(pkt.namespace, pkt.id, pkt.data)
            elif pkt.packet_type == packet.BINARY_EVENT or \
                    pkt.packet_type == packet.BINARY_ACK:
                self._binary_packet = pkt
            elif pkt.packet_type == packet.ERROR:
                self._handle_error(pkt.namespace)
            else:
                raise ValueError('Unknown packet type.')

    async def _handle_eio_disconnect(self):
        """Handle the Engine.IO disconnection event."""
        self.logger.info('Engine.IO connection dropped')
        for n in self.namespaces:
            await self._trigger_event('disconnect', namespace=n)
        await self._trigger_event('disconnect', namespace='/')
        self.callbacks = {}
        self._binary_packet = None
        if self.eio.state == 'connected' and self.reconnection:
            self._reconnect_task = self.start_background_task(
                self._handle_reconnect)

    def _engineio_client_class(self):
        return engineio.AsyncClient
