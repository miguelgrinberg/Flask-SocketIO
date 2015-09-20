import sys

import socketio
import flask

from .test_client import SocketIOTestClient


class SocketIO(object):
    """Create a Flask-SocketIO server.

    :param app: The flask application instance. If the application instance
                isn't known at the time this class is instantiated, then call
                ``socketio.init_app(app)`` once the application instance is
                available.
    :param kwargs: Socket.IO and Engine.IO server options.

    The Socket.IO options are detailed below:

    :param client_manager_class: The class that will manage the client list.
                                 The default value is appropriate for most
                                 cases.
    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``.
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

    :param async_mode: The library used for asynchronous operations. Valid
                       options are "threading", "eventlet" and "gevent". If
                       this argument is not given, "eventlet" is tried first,
                       then "gevent", and finally "threading". The websocket
                       transport is only supported in "eventlet" mode.
    :param ping_timeout: The time in seconds that the client waits for the
                         server to respond before disconnecting.
    :param ping_interval: The interval in seconds at which the client pings
                          the server.
    :param max_http_buffer_size: The maximum size of a message when using the
                                 polling transport.
    :param allow_upgrades: Whether to allow transport upgrades or not.
    :param http_compression: Whether to compress packages when using the
                             polling transport.
    :param compression_threshold: Only compress messages when their byte size
                                  is greater than this value.
    :param cookie: Name of the HTTP cookie that contains the client session
                   id. If set to ``None``, a cookie is not sent to the client.
    :param cors_allowed_origins: List of origins that are allowed to connect
                                 to this server. All origins are allowed by
                                 default.
    :param cors_credentials: Whether credentials (cookies, authentication) are
                             allowed in requests to this server.
    :param engineio_logger: To enable Engine.IO logging set to ``True`` or pass
                            a logger object to use. To disable logging set to
                            ``False``.
    """

    def __init__(self, app=None, **kwargs):
        self.app = None
        self.server = None
        self.server_options = None
        self.handlers = {}
        self.exception_handlers = {}
        self.default_exception_handler = None
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        if self.app is not None and self.app != app:
            raise RuntimeError('Cannot associate a SocketIO instance with '
                               'more than one application')
        if not hasattr(app, 'extensions'):
            app.extensions = {}  # pragma: no cover
        app.extensions['socketio'] = self
        self.server_options = kwargs
        self.app = app

    def on(self, message, namespace=None):
        """Decorator to register a SocketIO event handler.

        This decorator must be applied to SocketIO event handlers. Example::

            @socketio.on('my event', namespace='/chat')
            def handle_my_custom_event(json):
                print('received json: ' + str(json))

        :param message: The name of the event. Use ``'message'`` to define a
                        handler that takes a string payload, ``'json'`` to
                        define a handler that takes a JSON blob payload,
                        ``'connect'`` or ``'disconnect'`` to create handlers
                        for connection and disconnection events, or else, use a
                        custom event name, and use a JSON blob as payload.
        :param namespace: The namespace on which the handler is to be
                          registered. Defaults to the global namespace.
        """
        namespace = namespace or '/'

        def decorator(handler):
            def _handler(sid, *args):
                with self.app.request_context(self.server.environ[sid]):
                    if 'saved_session' in self.server.environ[sid]:
                        self._copy_session(
                            self.server.environ[sid]['saved_session'],
                            flask.session)
                    flask.request.sid = sid
                    flask.request.namespace = namespace
                    flask.request.event = {'message': message, 'args': args}
                    try:
                        if message == 'connect':
                            ret = handler()
                        else:
                            ret = handler(*args)
                    except:
                        err_handler = self.exception_handlers.get(
                            namespace, self.default_exception_handler)
                        if err_handler is None:
                            raise
                        type, value, traceback = sys.exc_info()
                        return err_handler(value)
                    self.server.environ[sid]['saved_session'] = {}
                    self._copy_session(
                        flask.session,
                        self.server.environ[sid]['saved_session'])
                    return ret
            if namespace not in self.handlers:
                self.handlers[namespace] = {}
            self.handlers[namespace][message] = _handler
        return decorator

    def on_error(self, namespace=None):
        """Decorator to define a custom error handler for SocketIO events.

        This decorator can be applied to a function that acts as an error
        handler for a namespace. This handler will be invoked when a SocketIO
        event handler raises an exception. The handler function must accept one
        argument, which is the exception raised. Example::

            @socketio.on_error(namespace='/chat')
            def chat_error_handler(e):
                print('An error has occurred: ' + str(e))

        :param namespace: The namespace for which to register the error
                          handler. Defaults to the global namespace.
        """
        namespace = namespace or '/'
        def decorator(exception_handler):
            if not callable(exception_handler):
                raise ValueError('exception_handler must be callable')
            self.exception_handlers[namespace] = exception_handler
        return decorator

    def on_error_default(self, exception_handler):
        """Decorator to define a default error handler for SocketIO events.

        This decorator can be applied to a function that acts as a default
        error handler for any namespaces that do not have a specific handler.
        Example::

            @socketio.on_error_default
            def error_handler(e):
                print('An error has occurred: ' + str(e))
        """
        if not callable(exception_handler):
            raise ValueError('exception_handler must be callable')
        self.default_exception_handler = exception_handler

    def emit(self, event, *args, **kwargs):
        """Emit a server generated SocketIO event.

        This function emits a user-specific SocketIO event to one or more
        connected clients. A JSON blob can be attached to the event as payload.
        This function can be used outside of a SocketIO event context, so it is
        appropriate to use when the server is the originator of an event, for
        example as a result of a regular HTTP message. Example::

            @app.route('/ping')
            def ping():
                socketio.emit('ping event', {'data': 42}, namespace='/chat')

        :param event: The name of the user event to emit.
        :param args: A dictionary with the JSON data to send as payload.
        :param namespace: The namespace under which the message is to be sent.
                          Defaults to the global namespace.
        :param room: Send the message to all the users in the given room. If
                     this parameter is not included, the event is sent to
                     all connected users.
        :param include_self: ``True`` to include the sender when broadcasting
                             or addressing a room, or ``False`` to send to
                             everyone but the sender.
        :param callback: If given, this function will be called to acknowledge
                         that the client has received the message. The
                         arguments that will be passed to the function are
                         those provided by the client. Callback functions can
                         only be used when addressing an individual client.
        """
        skip_sid = flask.request.sid \
            if not kwargs.get('include_self', True) else None
        self.server.emit(event, *args, namespace=kwargs.get('namespace', '/'),
                         room=kwargs.get('room'), skip_sid=skip_sid,
                         callback=kwargs.get('callback'))

    def send(self, data, json=False, namespace=None, room=None,
             callback=None, include_self=True):
        """Send a server-generated SocketIO message.

        This function sends a simple SocketIO message to one or more connected
        clients. The message can be a string or a JSON blob. This is a simpler
        version of ``emit()``, which should be preferred. This function can be
        used outside of a SocketIO event context, so it is appropriate to use
        when the server is the originator of an event.

        :param message: The message to send, either a string or a JSON blob.
        :param json: ``True`` if ``message`` is a JSON blob, ``False``
                     otherwise.
        :param namespace: The namespace under which the message is to be sent.
                          Defaults to the global namespace.
        :param room: Send the message only to the users in the given room. If
                     this parameter is not included, the message is sent to
                     all connected users.
        :param include_self: ``True`` to include the sender when broadcasting
                             or addressing a room, or ``False`` to send to
                             everyone but the sender.
        :param callback: If given, this function will be called to acknowledge
                         that the client has received the message. The
                         arguments that will be passed to the function are
                         those provided by the client. Callback functions can
                         only be used when addressing an individual client.
        """
        skip_sid = flask.request.sid if not include_self else None
        if json:
            self.emit('json', data, namespace=namespace, room=room,
                      skip_sid=skip_sid, callback=callback)
        else:
            self.emit('message', data, namespace=namespace, room=room,
                      skip_sid=skip_sid, callback=callback)

    def close_room(self, room, namespace=None):
        """Close a room.

        This function removes any users that are in the given room and then
        deletes the room from the server. This function can be used outside
        of a SocketIO event context.

        :param room: The name of the room to close.
        :param namespace: The namespace under which the room exists. Defaults
                          to the global namespace.
        """
        self.server.close_room(room, namespace)

    def run(self, app=None, host=None, port=None, **kwargs):
        """Run the SocketIO web server.

        :param app: The Flask application instance.
        :param host: The hostname or IP address for the server to listen on.
                     Defaults to 127.0.0.1.
        :param port: The port number for the server to listen on. Defaults to
                     5000.
        :param use_reloader: ``True`` to enable the Flask reloader, ``False``
                             to disable it.
        :param log_output: If ``True``, the server logs all incomming
                           connections. If ``False`` logging is disabled.
                           Defaults to ``True`` in debug mode, ``False``
                           otherwise.
        :param resource: The SocketIO resource name. Defaults to
                         ``'socket.io'``. Leave this as is unless you know what
                         you are doing.
        :param kwargs: Socket.IO and Engine.IO server options. See the
                       constructor of this class for the list of available
                       options.
        """
        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = app.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000

        if app is None:
            app = self.app
        else:
            self.app = app

        self.server_options.update(kwargs)
        test_mode = self.server_options.pop('test_mode', False)
        log_output = self.server_options.pop('log_output', app.debug)
        use_reloader = self.server_options.pop('use_reloader', app.debug)
        resource = self.server_options.pop('resource', 'socket.io')
        if resource.startswith('/'):
            resource = resource[1:]
        if app.debug:
            self.server_options['async_mode'] = 'threading'

        self.server = socketio.Server(**self.server_options)
        for namespace in self.handlers.keys():
            for message, handler in self.handlers[namespace].items():
                self.server.on(message, handler, namespace=namespace)

        app.wsgi_app = socketio.Middleware(self.server, app.wsgi_app,
                                           socketio_path=resource)

        if not test_mode:
            if self.server.eio.async_mode == 'threading':
                app.run(host=host, port=port, threaded=True,
                        use_reloader=use_reloader)
            elif self.server.eio.async_mode == 'eventlet':
                import eventlet
                eventlet.wsgi.server(eventlet.listen((host, port)), app,
                                     log_output=log_output, **kwargs)
            elif self.server.eio.async_mode == 'gevent':
                from gevent import pywsgi
                try:
                    from geventwebsocket.handler import WebSocketHandler
                    websocket = True
                except ImportError:
                    websocket = False

                log = 'default'
                if not log_output:
                    log = None
                if websocket:
                    pywsgi.WSGIServer((host, port), app,
                                      handler_class=WebSocketHandler,
                                      log=log).serve_forever()
                else:
                    pywsgi.WSGIServer((host, port), app,
                                      log=log).serve_forever()

    def test_client(self, app, namespace=None):
        """Return a simple SocketIO client that can be used for unit tests."""
        if self.server is None:
            self.run(app, test_mode=True)
        return SocketIOTestClient(app, self, namespace)

    def _copy_session(self, src, dest):
        for k in src:
            dest[k] = src[k]


def emit(event, *args, **kwargs):
    """Emit a SocketIO event.

    This function emits a user-specific SocketIO event to one or more connected
    clients. A JSON blob can be attached to the event as payload. This is a
    function that can only be called from a SocketIO event handler. Example::

        @socketio.on('my event')
        def handle_my_custom_event(json):
            emit('my response', {'data': 42})

    :param event: The name of the user event to emit.
    :param args: A dictionary with the JSON data to send as payload.
    :param namespace: The namespace under which the message is to be sent.
                      Defaults to the namespace used by the originating event.
                      An empty string can be used to use the global namespace.
    :param callback: Callback function to invoke with the client's
                     acknowledgement.
    :param broadcast: ``True`` to send the message to all connected clients, or
                      ``False`` to only reply to the sender of the originating
                      event.
    :param room: Send the message to all the users in the given room.
    :param include_self: ``True`` to include the sender when broadcasting or
                         addressing a room, or ``False`` to send to everyone
                         but the sender.
    """
    namespace = kwargs.get('namespace', flask.request.namespace)
    callback = kwargs.get('callback')
    broadcast = kwargs.get('broadcast')
    room = kwargs.get('room')
    if room is None and not broadcast:
        room = flask.request.sid
    include_self = kwargs.get('include_self', True)

    socketio = flask.current_app.extensions['socketio']
    return socketio.emit(event, *args, namespace=namespace, room=room,
                         include_self=include_self, callback=callback)


def send(message, **kwargs):
    """Send a SocketIO message.

    This function sends a simple SocketIO message to one or more connected
    clients. The message can be a string or a JSON blob. This is a simpler
    version of ``emit()``, which should be preferred. This is a function that
    can only be called from a SocketIO event handler.

    :param message: The message to send, either a string or a JSON blob.
    :param namespace: The namespace under which the message is to be sent.
                      Defaults to the namespace used by the originating event.
                      An empty string can be used to use the global namespace.
    :param callback: Callback function to invoke with the client's
                     acknowledgement.
    :param broadcast: ``True`` to send the message to all connected clients, or
                      ``False`` to only reply to the sender of the originating
                      event.
    :param room: Send the message to all the users in the given room.
    :param include_self: ``True`` to include the sender when broadcasting or
                         addressing a room, or ``False`` to send to everyone
                         but the sender.
    """
    namespace = kwargs.get('namespace', flask.request.namespace)
    callback = kwargs.get('callback')
    broadcast = kwargs.get('broadcast')
    room = kwargs.get('room')
    if room is None and not broadcast:
        room = flask.request.sid
    include_self = kwargs.get('include_self', True)

    socketio = flask.current_app.extensions['socketio']
    return socketio.send(message, namespace=namespace, room=room,
                         include_self=include_self, callback=callback)


def join_room(room):
    """Join a room.

    This function puts the user in a room, under the current namespace. The
    user and the namespace are obtained from the event context. This is a
    function that can only be called from a SocketIO event handler. Example::

        @socketio.on('join')
        def on_join(data):
            username = session['username']
            room = data['room']
            join_room(room)
            send(username + ' has entered the room.', room=room)

    :param room: The name of the room to join.
    """
    socketio = flask.current_app.extensions['socketio']
    socketio.server.enter_room(flask.request.sid, room,
                               namespace=flask.request.namespace)


def leave_room(room):
    """Leave a room.

    This function removes the user from a room, under the current namespace.
    The user and the namespace are obtained from the event context. This is
    a function that can only be called from a SocketIO event handler. Example::

        @socketio.on('leave')
        def on_leave(data):
            username = session['username']
            room = data['room']
            leave_room(room)
            send(username + ' has left the room.', room=room)

    :param room: The name of the room to leave.
    """
    socketio = flask.current_app.extensions['socketio']
    socketio.server.leave_room(flask.request.sid, room,
                               namespace=flask.request.namespace)


def close_room(room):
    """Close a room.

    This function removes any users that are in the given room and then deletes
    the room from the server. This is a function that can only be called from
    a SocketIO event handler.

    :param room: The name of the room to close.
    """
    socketio = flask.current_app.extensions['socketio']
    socketio.server.close_room(room, namespace=flask.request.namespace)


def rooms():
    """Return a list of the rooms the client is in.

    This function returns all the rooms the client has entered, including its
    own room, assigned by the Socket.IO server. This is a function that can
    only be called from a SocketIO event handler.
    """
    socketio = flask.current_app.extensions['socketio']
    return socketio.server.rooms(flask.request.sid,
                                 namespace=flask.request.namespace)


def disconnect(silent=False):
    """Disconnect the client.

    This function terminates the connection with the client. As a result of
    this call the client will receive a disconnect event. Example::

        @socketio.on('message')
        def receive_message(msg):
            if is_banned(session['username']):
                disconnect()
            # ...

    :param silent: this option is deprecated.
    """
    socketio = flask.current_app.extensions['socketio']
    return socketio.server.disconnect(flask.request.sid,
                                      namespace=flask.request.namespace)
