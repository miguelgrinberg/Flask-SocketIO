import logging

import engineio
import six

from . import base_manager
from . import packet
from . import namespace

default_logger = logging.getLogger('socketio.server')


class Server(object):
    """A Socket.IO server.

    This class implements a fully compliant Socket.IO web server with support
    for websocket and long-polling transports.

    :param client_manager: The client manager instance that will manage the
                           client list. When this is omitted, the client list
                           is stored in an in-memory structure, so the use of
                           multiple connected servers is not possible.
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
    :param async_handlers: If set to ``True``, event handlers are executed in
                           separate threads. To run handlers synchronously,
                           set to ``False``. The default is ``False``.
    :param kwargs: Connection parameters for the underlying Engine.IO server.

    The Engine.IO configuration supports the following settings:

    :param async_mode: The asynchronous model to use. See the Deployment
                       section in the documentation for a description of the
                       available options. Valid async modes are "threading",
                       "eventlet", "gevent" and "gevent_uwsgi". If this
                       argument is not given, "eventlet" is tried first, then
                       "gevent_uwsgi", then "gevent", and finally "threading".
                       The first async mode that has all its dependencies
                       installed is then one that is chosen.
    :param ping_timeout: The time in seconds that the client waits for the
                         server to respond before disconnecting. The default
                         is 60 seconds.
    :param ping_interval: The interval in seconds at which the client pings
                          the server. The default is 25 seconds.
    :param max_http_buffer_size: The maximum size of a message when using the
                                 polling transport. The default is 100,000,000
                                 bytes.
    :param allow_upgrades: Whether to allow transport upgrades or not. The
                           default is ``True``.
    :param http_compression: Whether to compress packages when using the
                             polling transport. The default is ``True``.
    :param compression_threshold: Only compress messages when their byte size
                                  is greater than this value. The default is
                                  1024 bytes.
    :param cookie: Name of the HTTP cookie that contains the client session
                   id. If set to ``None``, a cookie is not sent to the client.
                   The default is ``'io'``.
    :param cors_allowed_origins: List of origins that are allowed to connect
                                 to this server. All origins are allowed by
                                 default.
    :param cors_credentials: Whether credentials (cookies, authentication) are
                             allowed in requests to this server. The default is
                             ``True``.
    :param engineio_logger: To enable Engine.IO logging set to ``True`` or pass
                            a logger object to use. To disable logging set to
                            ``False``. The default is ``False``.
    """
    def __init__(self, client_manager=None, logger=False, binary=False,
                 json=None, async_handlers=False, **kwargs):
        engineio_options = kwargs
        engineio_logger = engineio_options.pop('engineio_logger', None)
        if engineio_logger is not None:
            engineio_options['logger'] = engineio_logger
        if json is not None:
            packet.Packet.json = json
            engineio_options['json'] = json
        engineio_options['async_handlers'] = False
        self.eio = self._engineio_server_class()(**engineio_options)
        self.eio.on('connect', self._handle_eio_connect)
        self.eio.on('message', self._handle_eio_message)
        self.eio.on('disconnect', self._handle_eio_disconnect)
        self.binary = binary

        self.environ = {}
        self.handlers = {}
        self.namespace_handlers = {}

        self._binary_packet = {}

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

        if client_manager is None:
            client_manager = base_manager.BaseManager()
        self.manager = client_manager
        self.manager.set_server(self)
        self.manager_initialized = False

        self.async_handlers = async_handlers

        self.async_mode = self.eio.async_mode

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
            @socket_io.on('connect', namespace='/chat')
            def connect_handler(sid, environ):
                print('Connection request')
                if environ['REMOTE_ADDR'] in blacklisted:
                    return False  # reject

            # as a method:
            def message_handler(sid, msg):
                print('Received message: ', msg)
                eio.send(sid, 'response')
            socket_io.on('message', namespace='/chat', message_handler)

        The handler function receives the ``sid`` (session ID) for the
        client as first argument. The ``'connect'`` event handler receives the
        WSGI environment as a second argument, and can return ``False`` to
        reject the connection. The ``'message'`` handler and handlers for
        custom event names receive the message payload as a second argument.
        Any values returned from a message handler will be passed to the
        client's acknowledgement callback function if it exists. The
        ``'disconnect'`` handler does not take a second argument.
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
        if not isinstance(namespace_handler, namespace.Namespace):
            raise ValueError('Not a namespace instance')
        if self.is_asyncio_based() != namespace_handler.is_asyncio_based():
            raise ValueError('Not a valid namespace class for this server')
        namespace_handler._set_server(self)
        self.namespace_handlers[namespace_handler.namespace] = \
            namespace_handler

    def emit(self, event, data=None, room=None, skip_sid=None, namespace=None,
             callback=None, **kwargs):
        """Emit a custom event to one or more connected clients.

        :param event: The event name. It can be any string. The event names
                      ``'connect'``, ``'message'`` and ``'disconnect'`` are
                      reserved and should not be used.
        :param data: The data to send to the client or clients. Data can be of
                     type ``str``, ``bytes``, ``list`` or ``dict``. If a
                     ``list`` or ``dict``, the data will be serialized as JSON.
        :param room: The recipient of the message. This can be set to the
                     session ID of a client to address that client's room, or
                     to any custom room created by the application, If this
                     argument is omitted the event is broadcasted to all
                     connected clients.
        :param skip_sid: The session ID of a client to skip when broadcasting
                         to a room or to all clients. This can be used to
                         prevent a message from being sent to the sender.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the event is emitted to the
                          default namespace.
        :param callback: If given, this function will be called to acknowledge
                         the the client has received the message. The arguments
                         that will be passed to the function are those provided
                         by the client. Callback functions can only be used
                         when addressing an individual client.
        :param ignore_queue: Only used when a message queue is configured. If
                             set to ``True``, the event is emitted to the
                             clients directly, without going through the queue.
                             This is more efficient, but only works when a
                             single server process is used. It is recommended
                             to always leave this parameter with its default
                             value of ``False``.
        """
        namespace = namespace or '/'
        self.logger.info('emitting event "%s" to %s [%s]', event,
                         room or 'all', namespace)
        self.manager.emit(event, data, namespace, room, skip_sid, callback,
                          **kwargs)

    def send(self, data, room=None, skip_sid=None, namespace=None,
             callback=None, **kwargs):
        """Send a message to one or more connected clients.

        This function emits an event with the name ``'message'``. Use
        :func:`emit` to issue custom event names.

        :param data: The data to send to the client or clients. Data can be of
                     type ``str``, ``bytes``, ``list`` or ``dict``. If a
                     ``list`` or ``dict``, the data will be serialized as JSON.
        :param room: The recipient of the message. This can be set to the
                     session ID of a client to address that client's room, or
                     to any custom room created by the application, If this
                     argument is omitted the event is broadcasted to all
                     connected clients.
        :param skip_sid: The session ID of a client to skip when broadcasting
                         to a room or to all clients. This can be used to
                         prevent a message from being sent to the sender.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the event is emitted to the
                          default namespace.
        :param callback: If given, this function will be called to acknowledge
                         the the client has received the message. The arguments
                         that will be passed to the function are those provided
                         by the client. Callback functions can only be used
                         when addressing an individual client.
        :param ignore_queue: Only used when a message queue is configured. If
                             set to ``True``, the event is emitted to the
                             clients directly, without going through the queue.
                             This is more efficient, but only works when a
                             single server process is used. It is recommended
                             to always leave this parameter with its default
                             value of ``False``.
        """
        self.emit('message', data, room, skip_sid, namespace, callback,
                  **kwargs)

    def enter_room(self, sid, room, namespace=None):
        """Enter a room.

        This function adds the client to a room. The :func:`emit` and
        :func:`send` functions can optionally broadcast events to all the
        clients in a room.

        :param sid: Session ID of the client.
        :param room: Room name. If the room does not exist it is created.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the default namespace is used.
        """
        namespace = namespace or '/'
        self.logger.info('%s is entering room %s [%s]', sid, room, namespace)
        self.manager.enter_room(sid, namespace, room)

    def leave_room(self, sid, room, namespace=None):
        """Leave a room.

        This function removes the client from a room.

        :param sid: Session ID of the client.
        :param room: Room name.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the default namespace is used.
        """
        namespace = namespace or '/'
        self.logger.info('%s is leaving room %s [%s]', sid, room, namespace)
        self.manager.leave_room(sid, namespace, room)

    def close_room(self, room, namespace=None):
        """Close a room.

        This function removes all the clients from the given room.

        :param room: Room name.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the default namespace is used.
        """
        namespace = namespace or '/'
        self.logger.info('room %s is closing [%s]', room, namespace)
        self.manager.close_room(room, namespace)

    def rooms(self, sid, namespace=None):
        """Return the rooms a client is in.

        :param sid: Session ID of the client.
        :param namespace: The Socket.IO namespace for the event. If this
                          argument is omitted the default namespace is used.
        """
        namespace = namespace or '/'
        return self.manager.get_rooms(sid, namespace)

    def get_session(self, sid, namespace=None):
        """Return the user session for a client.

        :param sid: The session id of the client.
        :param namespace: The Socket.IO namespace. If this argument is omitted
                          the default namespace is used.

        The return value is a dictionary. Modifications made to this
        dictionary are not guaranteed to be preserved unless
        ``save_session()`` is called, or when the ``session`` context manager
        is used.
        """
        namespace = namespace or '/'
        eio_session = self.eio.get_session(sid)
        return eio_session.setdefault(namespace, {})

    def save_session(self, sid, session, namespace=None):
        """Store the user session for a client.

        :param sid: The session id of the client.
        :param session: The session dictionary.
        :param namespace: The Socket.IO namespace. If this argument is omitted
                          the default namespace is used.
        """
        namespace = namespace or '/'
        eio_session = self.eio.get_session(sid)
        eio_session[namespace] = session

    def session(self, sid, namespace=None):
        """Return the user session for a client with context manager syntax.

        :param sid: The session id of the client.

        This is a context manager that returns the user session dictionary for
        the client. Any changes that are made to this dictionary inside the
        context manager block are saved back to the session. Example usage::

            @sio.on('connect')
            def on_connect(sid, environ):
                username = authenticate_user(environ)
                if not username:
                    return False
                with sio.session(sid) as session:
                    session['username'] = username

            @sio.on('message')
            def on_message(sid, msg):
                with sio.session(sid) as session:
                    print('received message from ', session['username'])
        """
        class _session_context_manager(object):
            def __init__(self, server, sid, namespace):
                self.server = server
                self.sid = sid
                self.namespace = namespace
                self.session = None

            def __enter__(self):
                self.session = self.server.get_session(sid,
                                                       namespace=namespace)
                return self.session

            def __exit__(self, *args):
                self.server.save_session(sid, self.session,
                                         namespace=namespace)

        return _session_context_manager(self, sid, namespace)

    def disconnect(self, sid, namespace=None):
        """Disconnect a client.

        :param sid: Session ID of the client.
        :param namespace: The Socket.IO namespace to disconnect. If this
                          argument is omitted the default namespace is used.
        """
        namespace = namespace or '/'
        if self.manager.is_connected(sid, namespace=namespace):
            self.logger.info('Disconnecting %s [%s]', sid, namespace)
            self.manager.pre_disconnect(sid, namespace=namespace)
            self._send_packet(sid, packet.Packet(packet.DISCONNECT,
                                                 namespace=namespace))
            self._trigger_event('disconnect', namespace, sid)
            self.manager.disconnect(sid, namespace=namespace)

    def transport(self, sid):
        """Return the name of the transport used by the client.

        The two possible values returned by this function are ``'polling'``
        and ``'websocket'``.

        :param sid: The session of the client.
        """
        return self.eio.transport(sid)

    def handle_request(self, environ, start_response):
        """Handle an HTTP request from the client.

        This is the entry point of the Socket.IO application, using the same
        interface as a WSGI application. For the typical usage, this function
        is invoked by the :class:`Middleware` instance, but it can be invoked
        directly when the middleware is not used.

        :param environ: The WSGI environment.
        :param start_response: The WSGI ``start_response`` function.

        This function returns the HTTP response body to deliver to the client
        as a byte sequence.
        """
        return self.eio.handle_request(environ, start_response)

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

    def _emit_internal(self, sid, event, data, namespace=None, id=None):
        """Send a message to a client."""
        if six.PY2 and not self.binary:
            binary = False  # pragma: nocover
        else:
            binary = None
        # tuples are expanded to multiple arguments, everything else is sent
        # as a single argument
        if isinstance(data, tuple):
            data = list(data)
        else:
            data = [data]
        self._send_packet(sid, packet.Packet(packet.EVENT, namespace=namespace,
                                             data=[event] + data, id=id,
                                             binary=binary))

    def _send_packet(self, sid, pkt):
        """Send a Socket.IO packet to a client."""
        encoded_packet = pkt.encode()
        if isinstance(encoded_packet, list):
            binary = False
            for ep in encoded_packet:
                self.eio.send(sid, ep, binary=binary)
                binary = True
        else:
            self.eio.send(sid, encoded_packet, binary=False)

    def _handle_connect(self, sid, namespace):
        """Handle a client connection request."""
        namespace = namespace or '/'
        self.manager.connect(sid, namespace)
        if self._trigger_event('connect', namespace, sid,
                               self.environ[sid]) is False:
            self.manager.disconnect(sid, namespace)
            self._send_packet(sid, packet.Packet(packet.ERROR,
                                                 namespace=namespace))
            if sid in self.environ:  # pragma: no cover
                del self.environ[sid]
            return False
        else:
            self._send_packet(sid, packet.Packet(packet.CONNECT,
                                                 namespace=namespace))

    def _handle_disconnect(self, sid, namespace):
        """Handle a client disconnect."""
        namespace = namespace or '/'
        if namespace == '/':
            namespace_list = list(self.manager.get_namespaces())
        else:
            namespace_list = [namespace]
        for n in namespace_list:
            if n != '/' and self.manager.is_connected(sid, n):
                self._trigger_event('disconnect', n, sid)
                self.manager.disconnect(sid, n)
        if namespace == '/' and self.manager.is_connected(sid, namespace):
            self._trigger_event('disconnect', '/', sid)
            self.manager.disconnect(sid, '/')
            if sid in self.environ:
                del self.environ[sid]

    def _handle_event(self, sid, namespace, id, data):
        """Handle an incoming client event."""
        namespace = namespace or '/'
        self.logger.info('received event "%s" from %s [%s]', data[0], sid,
                         namespace)
        if self.async_handlers:
            self.start_background_task(self._handle_event_internal, self, sid,
                                       data, namespace, id)
        else:
            self._handle_event_internal(self, sid, data, namespace, id)

    def _handle_event_internal(self, server, sid, data, namespace, id):
        r = server._trigger_event(data[0], namespace, sid, *data[1:])
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
            server._send_packet(sid, packet.Packet(packet.ACK,
                                                   namespace=namespace,
                                                   id=id, data=data,
                                                   binary=binary))

    def _handle_ack(self, sid, namespace, id, data):
        """Handle ACK packets from the client."""
        namespace = namespace or '/'
        self.logger.info('received ack from %s [%s]', sid, namespace)
        self.manager.trigger_callback(sid, namespace, id, data)

    def _trigger_event(self, event, namespace, *args):
        """Invoke an application event handler."""
        # first see if we have an explicit handler for the event
        if namespace in self.handlers and event in self.handlers[namespace]:
            return self.handlers[namespace][event](*args)

        # or else, forward the event to a namespace handler if one exists
        elif namespace in self.namespace_handlers:
            return self.namespace_handlers[namespace].trigger_event(
                event, *args)

    def _handle_eio_connect(self, sid, environ):
        """Handle the Engine.IO connection event."""
        if not self.manager_initialized:
            self.manager_initialized = True
            self.manager.initialize()
        self.environ[sid] = environ
        return self._handle_connect(sid, '/')

    def _handle_eio_message(self, sid, data):
        """Dispatch Engine.IO messages."""
        if sid in self._binary_packet:
            pkt = self._binary_packet[sid]
            if pkt.add_attachment(data):
                del self._binary_packet[sid]
                if pkt.packet_type == packet.BINARY_EVENT:
                    self._handle_event(sid, pkt.namespace, pkt.id, pkt.data)
                else:
                    self._handle_ack(sid, pkt.namespace, pkt.id, pkt.data)
        else:
            pkt = packet.Packet(encoded_packet=data)
            if pkt.packet_type == packet.CONNECT:
                self._handle_connect(sid, pkt.namespace)
            elif pkt.packet_type == packet.DISCONNECT:
                self._handle_disconnect(sid, pkt.namespace)
            elif pkt.packet_type == packet.EVENT:
                self._handle_event(sid, pkt.namespace, pkt.id, pkt.data)
            elif pkt.packet_type == packet.ACK:
                self._handle_ack(sid, pkt.namespace, pkt.id, pkt.data)
            elif pkt.packet_type == packet.BINARY_EVENT or \
                    pkt.packet_type == packet.BINARY_ACK:
                self._binary_packet[sid] = pkt
            elif pkt.packet_type == packet.ERROR:
                raise ValueError('Unexpected ERROR packet.')
            else:
                raise ValueError('Unknown packet type.')

    def _handle_eio_disconnect(self, sid):
        """Handle Engine.IO disconnect event."""
        self._handle_disconnect(sid, '/')

    def _engineio_server_class(self):
        return engineio.Server
