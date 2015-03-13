import os
import sys

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from flask import request, session, json
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader
from werkzeug._internal import _log

from test_client import SocketIOTestClient


class _SocketIOMiddleware(object):
    def __init__(self, app, socketio):
        self.app = app
        if app.debug:
            app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
        self.wsgi_app = app.wsgi_app
        self.socketio = socketio

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')
        if path is not None and path.startswith('socket.io'):
            if 'socketio' not in environ:
                raise RuntimeError('You need to use a gevent-socketio server.')
            socketio_manage(environ, self.socketio._get_namespaces(), self.app,
                            json_loads=json.loads, json_dumps=json.dumps)
        else:
            return self.wsgi_app(environ, start_response)


class SocketIO(object):
    """Create a Flask-SocketIO server.

    :param app: The flask application instance. If the application instance
                isn't known at the time this class is instantiated, then call
                ``socketio.init_app(app)`` once the application instance is
                available.
    """

    def __init__(self, app=None):
        if app:
            self.init_app(app)
        self.messages = {}
        self.rooms = {}
        self.server = None

        self.exception_handlers = {}
        self.default_exception_handler = None

    def init_app(self, app):
        app.wsgi_app = _SocketIOMiddleware(app, self)

    def _get_namespaces(self, base_namespace=BaseNamespace):
        class GenericNamespace(base_namespace):
            socketio = self
            base_emit = base_namespace.emit
            base_send = base_namespace.send

            def initialize(self):
                self.rooms = set()

            def process_event(self, packet):
                if self.socketio.server is None:
                    self.socketio.server = self.environ['socketio'].server
                message = packet['name']
                args = packet['args']
                app = self.request
                return self.socketio._dispatch_message(app, self, message, args)

            def join_room(self, room):
                if self.socketio._join_room(self, room):
                    self.rooms.add(room)

            def leave_room(self, room):
                if self.socketio._leave_room(self, room):
                    self.rooms.remove(room)

            def close_room(self, room):
                self.socketio._close_room(self, room)

            def recv_connect(self):
                if self.socketio.server is None:
                    self.socketio.server = self.environ['socketio'].server
                ret = super(GenericNamespace, self).recv_connect()
                app = self.request
                self.socketio._dispatch_message(app, self, 'connect')
                return ret

            def recv_disconnect(self):
                if self.socketio.server is None:
                    self.socketio.server = self.environ['socketio'].server
                app = self.request
                self.socketio._dispatch_message(app, self, 'disconnect')
                self.socketio._leave_all_rooms(self)
                return super(GenericNamespace, self).recv_disconnect()

            def recv_message(self, data):
                if self.socketio.server is None:
                    self.socketio.server = self.environ['socketio'].server
                app = self.request
                return self.socketio._dispatch_message(app, self, 'message',
                                                       [data])

            def recv_json(self, data):
                if self.socketio.server is None:
                    self.socketio.server = self.environ['socketio'].server
                app = self.request
                return self.socketio._dispatch_message(app, self, 'json',
                                                       [data])

            def emit(self, event, *args, **kwargs):
                ns_name = kwargs.pop('namespace', None)
                broadcast = kwargs.pop('broadcast', False)
                room = kwargs.pop('room', None)
                if broadcast or room:
                    if ns_name is None:
                        ns_name = self.ns_name
                    return self.socketio.emit(event, *args, namespace=ns_name,
                                              room=room)
                if ns_name is None:
                    return self.base_emit(event, *args, **kwargs)
                return request.namespace.socket[ns_name].base_emit(event, *args,
                                                                   **kwargs)

            def send(self, message, json=False, ns_name=None, callback=None,
                     broadcast=False, room=None):
                if broadcast or room:
                    if ns_name is None:
                        ns_name = self.ns_name
                    return self.socketio.send(message, json, ns_name, room)
                if ns_name is None:
                    return request.namespace.base_send(message, json, callback)
                return request.namespace.socket[ns_name].base_send(message,
                                                                   json,
                                                                   callback)

            def disconnect(self, silent=False):
                self.socketio._leave_all_rooms(self)
                return super(GenericNamespace, self).disconnect(silent)

        namespaces = dict((ns_name, GenericNamespace)
                          for ns_name in self.messages)
        return namespaces

    def _dispatch_message(self, app, namespace, message, args=[]):
        if namespace.ns_name not in self.messages:
            return
        if message not in self.messages[namespace.ns_name]:
            return
        with app.request_context(namespace.environ):
            request.namespace = namespace
            request.event = {
                "message": message,
                "args": args}
            for k, v in namespace.session.items():
                session[k] = v
            ret = self.messages[namespace.ns_name][message](*args)
            for k, v in session.items():
                namespace.session[k] = v
            return ret

    def _join_room(self, namespace, room):
        if namespace.ns_name not in self.rooms:
            self.rooms[namespace.ns_name] = {}
        if room not in self.rooms[namespace.ns_name]:
            self.rooms[namespace.ns_name][room] = set()
        if namespace not in self.rooms[namespace.ns_name][room]:
            self.rooms[namespace.ns_name][room].add(namespace)
            return True
        return False

    def _leave_room(self, namespace, room):
        if namespace.ns_name in self.rooms:
            if room in self.rooms[namespace.ns_name]:
                if namespace in self.rooms[namespace.ns_name][room]:
                    self.rooms[namespace.ns_name][room].remove(namespace)
                    if len(self.rooms[namespace.ns_name][room]) == 0:
                        del self.rooms[namespace.ns_name][room]
                        if len(self.rooms[namespace.ns_name]) == 0:
                            del self.rooms[namespace.ns_name]

                    return True
        return False

    def _close_room(self, namespace, room):
        self.close_room(room, namespace.ns_name)

    def _leave_all_rooms(self, namespace):
        if namespace.ns_name in self.rooms:
            for room in self.rooms[namespace.ns_name].copy():
                self._leave_room(namespace, room)

    def _on_message(self, message, handler, namespace=''):
        if namespace not in self.messages:
            self.messages[namespace] = {}
        self.messages[namespace][message] = handler

    def on(self, message, namespace=''):
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
        if namespace in self.exception_handlers or \
                self.default_exception_handler is not None:
            def decorator(event_handler):
                def func(*args, **kwargs):
                    try:
                        event_handler(*args, **kwargs)
                    except:
                        handler = self.exception_handlers.get(
                            namespace, self.default_exception_handler)
                        type, value, traceback = sys.exc_info()
                        handler(value)
                self._on_message(message, func, namespace)
                return func
        else:
            def decorator(event_handler):
                self._on_message(message, event_handler, namespace)
                return event_handler
        return decorator

    def on_error(self, namespace=''):
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
        """
        ns_name = kwargs.pop('namespace', '')
        room = kwargs.pop('room', None)
        if room is not None:
            for client in self.rooms.get(ns_name, {}).get(room, set()):
                client.base_emit(event, *args, **kwargs)
        elif self.server:
            for sessid, socket in self.server.sockets.items():
                if socket.active_ns.get(ns_name):
                    socket[ns_name].base_emit(event, *args, **kwargs)

    def send(self, message, json=False, namespace=None, room=None):
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
        """
        ns_name = namespace
        if ns_name is None:
            ns_name = ''
        if room:
            for client in self.rooms.get(ns_name, {}).get(room, set()):
                client.base_send(message, json)
        else:
            if self.server:
                for sessid, socket in self.server.sockets.items():
                    if socket.active_ns.get(ns_name):
                        socket[ns_name].base_send(message, json)

    def close_room(self, room, namespace=''):
        """Close a room.

        This function removes any users that are in the given room and then
        deletes the room from the server. This function can be used outside
        of a SocketIO event context.

        :param room: The name of the room to close.
        :param namespace: The namespace under which the room exists. Defaults
                          to the global namespace.
        """
        if namespace in self.rooms:
            if room in self.rooms[namespace]:
                for ns in self.rooms[namespace][room].copy():
                    self._leave_room(ns, room)

    def run(self, app, host=None, port=None, **kwargs):
        """Run the SocketIO web server.

        :param app: The Flask application instance.
        :param host: The hostname or IP address for the server to listen on.
                     Defaults to 127.0.0.1.
        :param port: The port number for the server to listen on. Defaults to
                     5000.
        :param use_reloader: ``True`` to enable the Flask reloader, ``False``
                             to disable it.
        :param resource: The SocketIO resource name. Defaults to
                         ``'socket.io'``. Leave this as is unless you know what
                         you are doing.
        :param transports: Optional list of transports to allow. List of
                           strings, each string should be one of
                           handler.SocketIOHandler.handler_types.
        :param policy_server: Boolean describing whether or not to use the
                              Flash policy server.  Defaults to ``True``.
        :param policy_listener: A tuple containing (host, port) for the
                                policy server. This is optional and used only
                                if policy server is set to true.  Defaults to
                                0.0.0.0:843.
        :param heartbeat_interval: The timeout for the server, we should
                                   receive a heartbeat from the client within
                                   this interval. This should be less than the
                                   ``heartbeat_timeout``.
        :param heartbeat_timeout: The timeout for the client when it should
                                  send a new heartbeat to the server. This
                                  value is sent to the client after a
                                  successful handshake.
        :param close_timeout: The timeout for the client, when it closes the
                              connection it still X amounts of seconds to do
                              re-open of the connection. This value is sent to
                              the client after a successful handshake.
        :param log_file: The file in which you want the PyWSGI server to write
                         its access log.  If not specified, it is sent to
                         ``stderr`` (with gevent 0.13).
        """
        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = app.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000
        resource = kwargs.pop('resource', 'socket.io')
        use_reloader = kwargs.pop('use_reloader', app.debug)

        self.server = SocketIOServer((host, port), app.wsgi_app,
                                     resource=resource, **kwargs)
        if use_reloader:
            # monkey patching is required by the reloader
            from gevent import monkey
            monkey.patch_all()

            def run_server():
                self.server.serve_forever()
            if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
                _log('info', ' * Running on http://%s:%d/' % (host, port))
            run_with_reloader(run_server)
        else:
            _log('info', ' * Running on http://%s:%d/' % (host, port))
            self.server.serve_forever()

    def test_client(self, app, namespace=None):
        """Return a simple SocketIO client that can be used for unit tests."""
        return SocketIOTestClient(app, self, namespace)


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
    """
    return request.namespace.emit(event, *args, **kwargs)


def send(message, json=False, namespace=None, callback=None, broadcast=False,
         room=None):
    """Send a SocketIO message.

    This function sends a simple SocketIO message to one or more connected
    clients. The message can be a string or a JSON blob. This is a simpler
    version of ``emit()``, which should be preferred. This is a function that
    can only be called from a SocketIO event handler.

    :param message: The message to send, either a string or a JSON blob.
    :param json: ``True`` if ``message`` is a JSON blob, ``False`` otherwise.
    :param namespace: The namespace under which the message is to be sent.
                      Defaults to the namespace used by the originating event.
                      An empty string can be used to use the global namespace.
    :param callback: Callback function to invoke with the client's
                     acknowledgement.
    :param broadcast: ``True`` to send the message to all connected clients, or
                      ``False`` to only reply to the sender of the originating
                      event.
    :param room: Send the message to all the users in the given room.
    """
    return request.namespace.send(message, json, namespace, callback, broadcast,
                                  room)


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
    return request.namespace.join_room(room)


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
    return request.namespace.leave_room(room)


def close_room(room):
    """Close a room.

    This function removes any users that are in the given room and then deletes
    the room from the server. This is a function that can only be called from
    a SocketIO event handler.

    :param room: The name of the room to close.
    """
    return request.namespace.close_room(room)


def disconnect(silent=False):
    """Disconnect the client.

    This function terminates the connection with the client. As a result of
    this call the client will receive a disconnect event. Example::

        @socketio.on('message')
        def receive_message(msg):
            if is_banned(session['username']):
                disconnect()
            # ...

    :param silent: close the connection, but do not actually send a disconnect
                   packet to the client.
    """
    return request.namespace.disconnect(silent)
