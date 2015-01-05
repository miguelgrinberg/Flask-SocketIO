"""
This module contains a collection of auxiliary mock objects used by
unit tests.
"""


class TestServer(object):
    counter = 0

    def __init__(self):
        self.sockets = {}

    def new_socket(self):
        socket = TestSocket(self, self.counter)
        self.sockets[self.counter] = socket
        self.counter += 1
        return socket

    def remove_socket(self, socket):
        for id, s in self.sockets.items():
            if s == socket:
                del self.sockets[id]
                return


class TestSocket(object):
    def __init__(self, server, sessid):
        self.server = server
        self.sessid = sessid
        self.active_ns = {}

    def __getitem__(self, ns_name):
        return self.active_ns[ns_name]


class TestBaseNamespace(object):
    def __init__(self, ns_name, socket, request=None):
        from werkzeug.test import EnvironBuilder
        self.environ = EnvironBuilder().get_environ()
        self.ns_name = ns_name
        self.socket = socket
        self.request = request
        self.session = {}
        self.received = []
        self.initialize()

    def initialize(self):
        pass

    def recv_connect(self):
        pass

    def recv_disconnect(self):
        pass

    def emit(self, event, *args, **kwargs):
        self.received.append({'name': event, 'args': args})
        callback = kwargs.pop('callback', None)
        if callback:
            callback()

    def send(self, message, json=False, callback=None):
        if not json:
            self.received.append({'name': 'message', 'args': message})
        else:
            self.received.append({'name': 'json', 'args': message})
        if callback:
            callback()


class SocketIOTestClient(object):
    server = TestServer()

    def __init__(self, app, socketio, namespace=''):
        self.socketio = socketio
        self.socketio.server = self.server
        self.socket = self.server.new_socket()
        self.connect(app, namespace)

    def __del__(self):
        self.server.remove_socket(self.socket)

    def connect(self, app, namespace=None):
        if self.socket.active_ns.get(namespace):
            self.disconnect(namespace)
        if namespace is None or namespace == '/':
            namespace = ''
        self.socket.active_ns[namespace] = \
            self.socketio._get_namespaces(
                TestBaseNamespace)[namespace](namespace, self.socket, app)
        self.socket[namespace].recv_connect()

    def disconnect(self, namespace=None):
        if namespace is None or namespace == '/':
            namespace = ''
        if self.socket[namespace]:
            self.socket[namespace].recv_disconnect()
            del self.socket.active_ns[namespace]

    def emit(self, event, *args, **kwargs):
        namespace = kwargs.pop('namespace', None)
        if namespace is None or namespace == '/':
            namespace = ''
        return self.socket[namespace].process_event({'name': event, 'args': args})

    def send(self, message, json=False, namespace=None):
        if namespace is None or namespace == '/':
            namespace = ''
        if not json:
            return self.socket[namespace].recv_message(message)
        else:
            return self.socket[namespace].recv_json(message)

    def get_received(self, namespace=None):
        if namespace is None or namespace == '/':
            namespace = ''
        received = self.socket[namespace].received
        self.socket[namespace].received = []
        return received
