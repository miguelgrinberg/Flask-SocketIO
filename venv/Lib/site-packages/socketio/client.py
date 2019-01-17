import itertools
import logging
import random

import engineio
import six

from . import exceptions
from . import namespace
from . import packet

default_logger = logging.getLogger('socketio.client')


class Client(object):
    """A Socket.IO client.

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
    def __init__(self, reconnection=True, reconnection_attempts=0,
                 reconnection_delay=1, reconnection_delay_max=5,
                 randomization_factor=0.5, logger=False, binary=False,
                 json=None, **kwargs):
        self.reconnection = reconnection
        self.reconnection_attempts = reconnection_attempts
        self.reconnection_delay = reconnection_delay
        self.reconnection_delay_max = reconnection_delay_max
        self.randomization_factor = randomization_factor
        self.binary = binary

        engineio_options = kwargs
        engineio_logger = engineio_options.pop('engineio_logger', None)
        if engineio_logger is not None:
            engineio_options['logger'] = engineio_logger
        if json is not None:
            packet.Packet.json = json
            engineio_options['json'] = json

        self.eio = self._engineio_client_class()(**engineio_options)
        self.eio.on('connect', self._handle_eio_connect)
        self.eio.on('message', self._handle_eio_message)
        self.eio.on('disconnect', self._handle_eio_disconnect)

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

        self.connection_url = None
        self.connection_headers = None
        self.connection_transports = None
        self.connection_namespaces = None
        self.socketio_path = None

        self.namespaces = []
        self.handlers = {}
        self.namespace_handlers = {}
        self.callbacks = {}
        self._binary_packet = None
        self._reconnect_task = None

    def is_asyncio_based(self):
        return False

    def on(self, event, handler=None, namespace=None):
        """Register an event handler.

        :param event: The event name. It can be any string. The event names
                      ``'connect'``, ``'message'`` and ``'disconnect'`` are
                      reserved and should not be used.
        :param handler: The function that should be invoked to handle the
                        event. When this parameter is not given, the method
                        acts as a decorator for the handler function.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the handler is associated with
                          the default namespace.

        Example usage::

            # as a decorator:
            @sio.on('connect')
            def connect_handler():
                print('Connected!')

            # as a method:
            def message_handler(msg):
                print('Received message: ', msg)
                sio.send( 'response')
            sio.on('message', message_handler)

        The ``'connect'`` event handler receives no arguments. The
        ``'message'`` handler and handlers for custom event names receive the
        message payload as only argument. Any values returned from a message
        handler will be passed to the client's acknowledgement callback
        function if it exists. The ``'disconnect'`` handler does not take
        arguments.
        """
        namespace = namespace or '/'

        def set_handler(handler):
            if namespace not in self.handlers:
                self.handlers[namespace] = {}
            self.handlers[namespace][event] = handler
            return handler

        if handler is None:
            return set_handler
        set_handler(handler)

    def register_namespace(self, namespace_handler):
        """Register a namespace handler object.

        :param namespace_handler: An instance of a :class:`Namespace`
                                  subclass that handles all the event traffic
                                  for a namespace.
        """
        if not isinstance(namespace_handler, namespace.ClientNamespace):
            raise ValueError('Not a namespace instance')
        if self.is_asyncio_based() != namespace_handler.is_asyncio_based():
            raise ValueError('Not a valid namespace class for this client')
        namespace_handler._set_client(self)
        self.namespace_handlers[namespace_handler.namespace] = \
            namespace_handler

    def connect(self, url, headers={}, transports=None,
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
            self.eio.connect(url, headers=headers, transports=transports,
                             engineio_path=socketio_path)
        except engineio.exceptions.ConnectionError as exc:
            six.raise_from(exceptions.ConnectionError(exc.args[0]), None)

    def wait(self):
        """Wait until the connection with the server ends.

        Client applications can use this function to block the main thread
        during the life of the connection.
        """
        while True:
            self.eio.wait()
            self.sleep(1)  # give the reconnect task time to start up
            if not self._reconnect_task:
                break
            self._reconnect_task.join()
            if self.eio.state != 'connected':
                break

    def emit(self, event, data=None, namespace=None, callback=None,
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
        self._send_packet(packet.Packet(packet.EVENT, namespace=namespace,
                                        data=[event] + data, id=id,
                                        binary=binary))
        if wait is True:
            print('1')
            if not callback_event.wait(timeout=timeout):
                raise exceptions.TimeoutError()
            print('2')
            return callback_args[0] if len(callback_args[0]) > 1 \
                else callback_args[0][0] if len(callback_args[0]) == 1 \
                    else None

    def send(self, data, namespace=None, callback=None, wait=False,
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
        """
        self.emit('message', data=data, namespace=namespace,
                  callback=callback, wait=wait, timeout=timeout)

    def disconnect(self):
        """Disconnect from the server."""
        for n in self.namespaces:
            self._trigger_event('disconnect', namespace=n)
            self._send_packet(packet.Packet(packet.DISCONNECT, namespace=n))
        self._trigger_event('disconnect', namespace='/')
        self._send_packet(packet.Packet(
            packet.DISCONNECT, namespace='/'))
        self.eio.disconnect(abort=True)

    def transport(self):
        """Return the name of the transport used by the client.

        The two possible values returned by this function are ``'polling'``
        and ``'websocket'``.
        """
        return self.eio.transport()

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

    def sleep(self, seconds=0):
        """Sleep for the requested amount of time using the appropriate async
        model.

        This is a utility function that applications can use to put a task to
        sleep without having to worry about using the correct call for the
        selected async mode.
        """
        return self.eio.sleep(seconds)

    def _send_packet(self, pkt):
        """Send a Socket.IO packet to the server."""
        encoded_packet = pkt.encode()
        if isinstance(encoded_packet, list):
            binary = False
            for ep in encoded_packet:
                self.eio.send(ep, binary=binary)
                binary = True
        else:
            self.eio.send(encoded_packet, binary=False)

    def _generate_ack_id(self, namespace, callback):
        """Generate a unique identifier for an ACK packet."""
        namespace = namespace or '/'
        if namespace not in self.callbacks:
            self.callbacks[namespace] = {0: itertools.count(1)}
        id = six.next(self.callbacks[namespace][0])
        self.callbacks[namespace][id] = callback
        return id

    def _handle_connect(self, namespace):
        namespace = namespace or '/'
        self.logger.info('Namespace {} is connected'.format(namespace))
        self._trigger_event('connect', namespace=namespace)
        if namespace == '/':
            for n in self.namespaces:
                self._send_packet(packet.Packet(packet.CONNECT, namespace=n))
        elif namespace not in self.namespaces:
            self.namespaces.append(namespace)

    def _handle_disconnect(self, namespace):
        namespace = namespace or '/'
        self._trigger_event('disconnect', namespace=namespace)
        if namespace in self.namespaces:
            self.namespaces.remove(namespace)

    def _handle_event(self, namespace, id, data):
        namespace = namespace or '/'
        self.logger.info('Received event "%s" [%s]', data[0], namespace)
        r = self._trigger_event(data[0], namespace, *data[1:])
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
            self._send_packet(packet.Packet(packet.ACK, namespace=namespace,
                              id=id, data=data, binary=binary))

    def _handle_ack(self, namespace, id, data):
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
            callback(*data)

    def _handle_error(self, namespace):
        namespace = namespace or '/'
        self.logger.info('Connection to namespace {} was rejected'.format(
            namespace))
        if namespace in self.namespaces:
            self.namespaces.remove(namespace)

    def _trigger_event(self, event, namespace, *args):
        """Invoke an application event handler."""
        # first see if we have an explicit handler for the event
        if namespace in self.handlers and event in self.handlers[namespace]:
            return self.handlers[namespace][event](*args)

        # or else, forward the event to a namespace handler if one exists
        elif namespace in self.namespace_handlers:
            return self.namespace_handlers[namespace].trigger_event(
                event, *args)

    def _handle_reconnect(self):
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
            self.sleep(delay)
            attempt_count += 1
            try:
                self.connect(self.connection_url,
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

    def _handle_eio_message(self, data):
        """Dispatch Engine.IO messages."""
        if self._binary_packet:
            pkt = self._binary_packet
            if pkt.add_attachment(data):
                self._binary_packet = None
                if pkt.packet_type == packet.BINARY_EVENT:
                    self._handle_event(pkt.namespace, pkt.id, pkt.data)
                else:
                    self._handle_ack(pkt.namespace, pkt.id, pkt.data)
        else:
            pkt = packet.Packet(encoded_packet=data)
            if pkt.packet_type == packet.CONNECT:
                self._handle_connect(pkt.namespace)
            elif pkt.packet_type == packet.DISCONNECT:
                self._handle_disconnect(pkt.namespace)
            elif pkt.packet_type == packet.EVENT:
                self._handle_event(pkt.namespace, pkt.id, pkt.data)
            elif pkt.packet_type == packet.ACK:
                self._handle_ack(pkt.namespace, pkt.id, pkt.data)
            elif pkt.packet_type == packet.BINARY_EVENT or \
                    pkt.packet_type == packet.BINARY_ACK:
                self._binary_packet = pkt
            elif pkt.packet_type == packet.ERROR:
                self._handle_error(pkt.namespace)
            else:
                raise ValueError('Unknown packet type.')

    def _handle_eio_disconnect(self):
        """Handle the Engine.IO disconnection event."""
        self.logger.info('Engine.IO connection dropped')
        for n in self.namespaces:
            self._trigger_event('disconnect', namespace=n)
        self._trigger_event('disconnect', namespace='/')
        self.callbacks = {}
        self._binary_packet = None
        if self.eio.state == 'connected' and self.reconnection:
            self._reconnect_task = self.start_background_task(
                self._handle_reconnect)

    def _engineio_client_class(self):
        return engineio.Client
