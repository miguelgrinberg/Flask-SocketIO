import sys

# make sure gevent-socketio is not installed, as it conflicts with
# python-socketio
gevent_socketio_found = True
try:
    from socketio import socketio_manage
except ImportError:
    gevent_socketio_found = False
if gevent_socketio_found:
    print('The gevent-socketio package is incompatible with this version of '
          'the Flask-SocketIO extension. Please uninstall it, and then '
          'install the latest version of python-socketio in its place.')
    sys.exit(1)

import socketio
import flask
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader

from .test_client import SocketIOTestClient


class _SocketIOMiddleware(socketio.Middleware):
    """This WSGI middleware simply exposes the Flask application in the WSGI
    environment before executing the request.
    """
    def __init__(self, socketio_app, flask_app, socketio_path='socket.io'):
        self.flask_app = flask_app
        super(_SocketIOMiddleware, self).__init__(socketio_app,
                                                  flask_app.wsgi_app,
                                                  socketio_path)

    def __call__(self, environ, start_response):
        environ['flask.app'] = self.flask_app
        return super(_SocketIOMiddleware, self).__call__(environ,
                                                         start_response)


class SocketIO(object):
    """Create a Flask-SocketIO server.

    :param app: The flask application instance. If the application instance
                isn't known at the time this class is instantiated, then call
                ``socketio.init_app(app)`` once the application instance is
                available.
    :param message_queue: A connection URL for a message queue service the
                          server can use for multi-process communication. A
                          message queue is not required when using a single
                          server process.
    :param channel: The channel name, when using a message queue. If a channel
                    isn't specified, a default channel will be used. If
                    multiple clusters of SocketIO processes need to use the
                    same message queue without interfering with each other, then
                    each cluster should use a different channel.
    :param resource: The SocketIO resource name. Defaults to ``'socket.io'``.
                     Leave this as is unless you know what you are doing.
    :param kwargs: Socket.IO and Engine.IO server options.

    The Socket.IO server options are detailed below:

    :param client_manager: The client manager instance that will manage the
                           client list. When this is omitted, the client list
                           is stored in an in-memory structure, so the use of
                           multiple connected servers is not possible. In most
                           cases, this argument does not need to be set
                           explicitly.
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

    The Engine.IO server configuration supports the following settings:

    :param async_mode: The library used for asynchronous operations. Valid
                       options are "threading", "eventlet" and "gevent". If
                       this argument is not given, "eventlet" is tried first,
                       then "gevent", and finally "threading". The websocket
                       transport is not supported in "ithreading" mode.
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
        self.server = None
        self.server_options = None
        self.wsgi_server = None
        self.handlers = []
        self.exception_handlers = {}
        self.default_exception_handler = None
        if app is not None or len(kwargs) > 0:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        if app is not None:
            if not hasattr(app, 'extensions'):
                app.extensions = {}  # pragma: no cover
            app.extensions['socketio'] = self
        self.server_options = kwargs

        if 'client_manager' not in self.server_options:
            url = kwargs.pop('message_queue', None)
            channel = kwargs.pop('channel', 'flask-socketio')
            write_only = app is None
            if url:
                if url.startswith('redis://'):
                    queue_class = socketio.RedisManager
                else:
                    queue_class = socketio.KombuManager
                queue = queue_class(url, channel=channel,
                                    write_only=write_only)
                self.server_options['client_manager'] = queue

        resource = kwargs.pop('resource', 'socket.io')
        if resource.startswith('/'):
            resource = resource[1:]
        self.server = socketio.Server(**self.server_options)
        for handler in self.handlers:
            self.server.on(handler[0], handler[1], namespace=handler[2])
        if app is not None:
            # here we attach the SocketIO middlware to the SocketIO object so it
            # can be referenced later if debug middleware needs to be inserted
            self.sockio_mw = _SocketIOMiddleware(self.server, app,
                                                 socketio_path=resource)
            app.wsgi_app = self.sockio_mw

    def on(self, message, namespace=None):
        """Decorator to register a SocketIO event handler.

        This decorator must be applied to SocketIO event handlers. Example::

            @socketio.on('my event', namespace='/chat')
            def handle_my_custom_event(json):
                print('received json: ' + str(json))

        :param message: The name of the event. This is normally a user defined
                        string, but a few event names are already defined. Use
                        ``'message'`` to define a handler that takes a string
                        payload, ``'json'`` to define a handler that takes a
                        JSON blob payload, ``'connect'`` or ``'disconnect'``
                        to create handlers for connection and disconnection
                        events.
        :param namespace: The namespace on which the handler is to be
                          registered. Defaults to the global namespace.
        """
        namespace = namespace or '/'

        def decorator(handler):
            def _handler(sid, *args):
                app = self.server.environ[sid]['flask.app']
                with app.request_context(self.server.environ[sid]):
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
                    if flask.session.modified:
                        self.server.environ[sid]['saved_session'] = {}
                        self._copy_session(
                            flask.session,
                            self.server.environ[sid]['saved_session'])
                    return ret
            if self.server:
                self.server.on(message, _handler, namespace=namespace)
            else:
                self.handlers.append((message, _handler, namespace))
            return _handler
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
            return exception_handler
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
        return exception_handler

    def emit(self, event, *args, **kwargs):
        """Emit a server generated SocketIO event.

        This function emits a SocketIO event to one or more connected clients.
        A JSON blob can be attached to the event as payload. This function can
        be used outside of a SocketIO event context, so it is appropriate to
        use when the server is the originator of an event, outside of any
        client context, such as in a regular HTTP request handler or a
        background task. Example::

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

    def run(self, app, host=None, port=None, **kwargs):
        """Run the SocketIO web server.

        :param app: The Flask application instance.
        :param host: The hostname or IP address for the server to listen on.
                     Defaults to 127.0.0.1.
        :param port: The port number for the server to listen on. Defaults to
                     5000.
        :param debug: ``True`` to start the server in debug mode, ``False`` to
                      start in normal mode.
        :param use_reloader: ``True`` to enable the Flask reloader, ``False``
                             to disable it.
        :param extra_files: A list of additional files that the Flask
                            reloader should watch. Defaults to ``None``
        :param log_output: If ``True``, the server logs all incomming
                           connections. If ``False`` logging is disabled.
                           Defaults to ``True`` in debug mode, ``False``
                           in normal mode. Unused when the threading async
                           mode is used.
        :param kwargs: Additional web server options. The web server options
                       are specific to the server used in each of the supported
                       async modes. Note that options provided here will
                       not be seen when using an external web server such
                       as gunicorn, since this method is not called in that
                       case.
        """
        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = app.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000

        debug = kwargs.pop('debug', app.debug)
        log_output = kwargs.pop('log_output', debug)
        use_reloader = kwargs.pop('use_reloader', debug)
        extra_files = kwargs.pop('extra_files', None)

        app.debug = debug
        if app.debug and self.server.eio.async_mode != 'threading':
            # put the debug middleware between the SocketIO middleware
            # and the Flask application instance
            #
            #    mw1   mw2   mw3   Flask app
            #     o ---- o ---- o ---- o
            #    /
            #   o Flask-SocketIO
            #    \  middleware
            #     o
            #  Flask-SocketIO WebSocket handler
            #
            # BECOMES
            #
            #  dbg-mw   mw1   mw2   mw3   Flask app
            #     o ---- o ---- o ---- o ---- o
            #    /
            #   o Flask-SocketIO
            #    \  middleware
            #     o
            #  Flask-SocketIO WebSocket handler
            #
            self.sockio_mw.wsgi_app = DebuggedApplication(self.sockio_mw.wsgi_app,
                                                          evalex=True)

        if self.server.eio.async_mode == 'threading':
            from werkzeug._internal import _log
            _log('warning', 'WebSocket transport not available. Install '
                            'eventlet or gevent and gevent-websocket for '
                            'improved performance.')
            app.run(host=host, port=port, threaded=True,
                    use_reloader=use_reloader, **kwargs)
        elif self.server.eio.async_mode == 'eventlet':
            def run_server():
                import eventlet
                eventlet_socket = eventlet.listen((host, port))

                # If provided an SSL argument, use an SSL socket
                ssl_args = ['keyfile', 'certfile', 'server_side', 'cert_reqs',
                            'ssl_version', 'ca_certs',
                            'do_handshake_on_connect', 'suppress_ragged_eofs',
                            'ciphers']
                ssl_params = {k: kwargs[k] for k in kwargs if k in ssl_args}
                if len(ssl_params) > 0:
                    for k in ssl_params:
                        kwargs.pop(k)
                    ssl_params['server_side'] = True  # Listening requires true
                    eventlet_socket = eventlet.wrap_ssl(eventlet_socket,
                                                        **ssl_params)

                eventlet.wsgi.server(eventlet_socket, app,
                                     log_output=log_output, **kwargs)

            if use_reloader:
                run_with_reloader(run_server, extra_files=extra_files)
            else:
                run_server()
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
                self.wsgi_server = pywsgi.WSGIServer(
                    (host, port), app, handler_class=WebSocketHandler,
                    log=log, **kwargs)
            else:
                self.wsgi_server = pywsgi.WSGIServer((host, port), app,
                                                     log=log)

            if use_reloader:
                # monkey patching is required by the reloader
                from gevent import monkey
                monkey.patch_all()

                def run_server():
                    self.wsgi_server.serve_forever()

                run_with_reloader(run_server, extra_files=extra_files)
            else:
                self.wsgi_server.serve_forever()

    def stop(self):
        """Stop a running SocketIO web server.

        This method must be called from a HTTP or SocketIO handler function.
        """
        if self.server.eio.async_mode == 'threading':
            func = flask.request.environ.get('werkzeug.server.shutdown')
            if func:
                func()
            else:
                raise RuntimeError('Cannot stop unknown web server')
        elif self.server.eio.async_mode == 'eventlet':
            raise SystemExit
        elif self.server.eio.async_mode == 'gevent':
            self.wsgi_server.stop()

    def test_client(self, app, namespace=None):
        """Return a simple SocketIO client that can be used for unit tests."""
        return SocketIOTestClient(app, self, namespace)

    def _copy_session(self, src, dest):
        for k in src:
            dest[k] = src[k]


def emit(event, *args, **kwargs):
    """Emit a SocketIO event.

    This function emits a SocketIO event to one or more connected clients. A
    JSON blob can be attached to the event as payload. This is a function that
    can only be called from a SocketIO event handler, as in obtains some
    information from the current client context. Example::

        @socketio.on('my event')
        def handle_my_custom_event(json):
            emit('my response', {'data': 42})

    :param event: The name of the user event to emit.
    :param args: A dictionary with the JSON data to send as payload.
    :param namespace: The namespace under which the message is to be sent.
                      Defaults to the namespace used by the originating event.
                      A ``'/'`` can be used to explicitly specify the global
                      namespace.
    :param callback: Callback function to invoke with the client's
                     acknowledgement.
    :param broadcast: ``True`` to send the message to all clients, or ``False``
                      to only reply to the sender of the originating event.
    :param room: Send the message to all the users in the given room. If this
                 argument is set, then broadcast is implied to be ``True``.
    :param include_self: ``True`` to include the sender when broadcasting or
                         addressing a room, or ``False`` to send to everyone
                         but the sender.
    """
    if 'namespace' in kwargs:
        namespace = kwargs['namespace']
    else:
        namespace = flask.request.namespace
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
