from gevent import monkey
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from flask import request, session
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader
from test_client import SocketIOTestClient

monkey.patch_all()


class SocketIOMiddleware(object):
    def __init__(self, app, socket):
        self.app = app
        if app.debug:
            app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
        self.wsgi_app = app.wsgi_app
        self.socket = socket

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')
        if path is not None and path.startswith('socket.io'):
            socketio_manage(environ, self.socket.get_namespaces(), self.app)
        else:
            return self.wsgi_app(environ, start_response)

class SocketIO(object):
    def __init__(self, app=None):
        if app:
            self.init_app(app)
        self.messages = {}
        self.rooms = {}

    def init_app(self, app):
        app.wsgi_app = SocketIOMiddleware(app, self)

    def get_namespaces(self, base_namespace=BaseNamespace):
        class GenericNamespace(base_namespace):
            socketio = self
            base_emit = base_namespace.emit
            base_send = base_namespace.send

            def initialize(self):
                self.rooms = set()

            def process_event(self, packet):
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

            def recv_connect(self):
                ret = super(GenericNamespace, self).recv_connect()
                app = self.request
                self.socketio._dispatch_message(app, self, 'connect')
                return ret

            def recv_disconnect(self):
                app = self.request
                self.socketio._dispatch_message(app, self, 'disconnect')
                for room in self.rooms.copy():
                    self.leave_room(room)
                return super(GenericNamespace, self).recv_disconnect()

            def recv_message(self, data):
                app = self.request
                return self.socketio._dispatch_message(app, self, 'message', [data])

            def recv_json(self, data):
                app = self.request
                return self.socketio._dispatch_message(app, self, 'json', [data])

            def emit(self, event, *args, **kwargs):
                ns_name = kwargs.pop('namespace', None)
                broadcast = kwargs.pop('broadcast', False)
                room = kwargs.pop('room', None)
                if broadcast or room:
                    if ns_name is None:
                        ns_name = self.ns_name
                    return self.socketio.emit(event, *args, namespace=ns_name, room=room)
                if ns_name is None:
                    return self.base_emit(event, *args, **kwargs)
                return request.namespace.socket[ns_name].base_emit(event, *args, **kwargs)

            def send(self, message, json=False, ns_name=None, callback=None,
                     broadcast=False, room=None):
                if broadcast or room:
                    if ns_name is None:
                        ns_name = self.ns_name
                    return self.socketio.send(message, json, ns_name, room)
                if ns_name is None:
                    return request.namespace.base_send(message, json, callback)
                return request.namespace.socket[ns_name].base_send(message, json, callback)

        namespaces = {}
        for ns_name in self.messages.keys():
            namespaces[ns_name] = GenericNamespace
        return namespaces

    def _dispatch_message(self, app, namespace, message, args=[]):
        if namespace.ns_name not in self.messages:
            return
        if message not in self.messages[namespace.ns_name]:
            return
        with app.request_context(namespace.environ):
            request.namespace = namespace
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
        
    def on_message(self, message, handler, **options):
        ns_name = options.pop('namespace', '')
        if ns_name not in self.messages:
            self.messages[ns_name] = {}
        self.messages[ns_name][message] = handler

    def on(self, message, **options):
        def decorator(f):
            self.on_message(message, f, **options)
            return f
        return decorator

    def emit(self, event, *args, **kwargs):
        ns_name = kwargs.pop('namespace', None)
        if ns_name is None:
            ns_name = ''
        room = kwargs.pop('room', None)
        if room:
            for client in self.rooms.get(ns_name, {}).get(room, set()):
                client.base_emit(event, *args, **kwargs)
        else:
            for sessid, socket in self.server.sockets.items():
                if socket.active_ns.get(ns_name):
                    socket[ns_name].base_emit(event, *args, **kwargs)

    def send(self, message, json=False, namespace=None, room=None):
        ns_name = namespace
        if ns_name is None:
            ns_name = ''
        if room:
            for client in self.rooms.get(ns_name, {}).get(room, set()):
                client.base_send(message, json)
        else:
            for sessid, socket in self.server.sockets.items():
                if socket.active_ns.get(ns_name):
                    socket[ns_name].base_send(message, json)

    def run(self, app, host=None, port=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = app.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000
        self.server = SocketIOServer((host, port), app.wsgi_app, resource='socket.io')
        if app.debug:
            @run_with_reloader
            def run_server():
                self.server.serve_forever()
            run_server()
        else:
            self.server.serve_forever()

    def test_client(self, app, namespace=None):
        return SocketIOTestClient(app, self, namespace)


def emit(event, *args, **kwargs):
    return request.namespace.emit(event, *args, **kwargs)

def send(message, json=False, namespace=None, callback=None, broadcast=False, room=None):
    return request.namespace.send(message, json, namespace, callback, broadcast, room)


def join_room(room):
    return request.namespace.join_room(room)


def leave_room(room):
    return request.namespace.leave_room(room)


def error(error_name, error_message, msg_id=None, quiet=False):
    return request.namespace.error(error_name, error_message, msg_id, quiet)


def disconnect(silent=False):
    return request.namespace.disconnect(silent)
