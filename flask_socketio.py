import logging
from gevent import monkey
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from flask import request, session
from flask.ctx import RequestContext
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader

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

    def init_app(self, app):
        app.wsgi_app = SocketIOMiddleware(app, self)

        # redirect socketio logging to Flask's app.logger
        logger = logging.getLogger('socketio.virtsocket')
        logger.addHandler(app.logger)

    def get_namespaces(self):
        class GenericNamespace(BaseNamespace):
            socketio = self
            base_emit = BaseNamespace.emit
            base_send = BaseNamespace.send

            def process_event(self, packet):
                message = packet['name']
                args = packet['args']
                app = self.request
                self.socketio.dispatch_message(app, self, message, args)

            def recv_connect(self):
                ret = super(GenericNamespace, self).recv_connect()
                app = self.request
                self.socketio.dispatch_message(app, self, 'connect')
                return ret

            def recv_disconnect(self):
                app = self.request
                self.socketio.dispatch_message(app, self, 'disconnect')
                return super(GenericNamespace, self).recv_disconnect()

            def recv_message(self, data):
                app = self.request
                self.socketio.dispatch_message(app, self, 'message', [data])

            def recv_json(self, data):
                app = self.request
                self.socketio.dispatch_message(app, self, 'json', [data])

            def emit(self, event, *args, **kwargs):
                namespace = kwargs.pop('namespace', None)
                broadcast = kwargs.pop('broadcast', False)
                if broadcast:
                    if namespace is None:
                        namespace = self.ns_name
                    callback = kwargs.pop('callback', None)
                    ret = None
                    for sessid, socket in self.socket.server.sockets.items():
                        if socket == self.socket:
                            ret = self.base_emit(event, *args, callback=callback, **kwargs)
                        else:
                            socket[namespace].base_emit(event, *args, **kwargs)
                    return ret
                if namespace is None:
                    return self.base_emit(event, *args, **kwargs)
                return request.namespace.socket[namespace].base_emit(event, *args, **kwargs)

            def send(message, json=False, namespace=None, callback=None, broadcast=False):
                if broadcast:
                    if namespace is None:
                        namespace = self.ns_name
                    ret = None
                    for sessid, socket in self.socket.server.sockets.items():
                        if socket == request.namespace.socket:
                            ret = self.base_send(message, json, callback=callback)
                        else:
                            socket[namespace].base_send(message, json)
                    return ret
                if namespace is None:
                    return request.namespace.base_send(message, json, callback)
                return request.namespace.socket[namespace].base_send(message, json, callback)

        namespaces = {}
        for namespace in self.messages.keys():
            if namespace == '/':
                namespace = ''
            namespaces[namespace] = GenericNamespace
        return namespaces

    def dispatch_message(self, app, namespace, message, args=[]):
        if namespace.ns_name not in self.messages:
            return
        if message not in self.messages[namespace.ns_name]:
            return
        with app.app_context():
            with RequestContext(app, namespace.environ):
                request.namespace = namespace
                for k, v in namespace.session.items():
                    session[k] = v
                self.messages[namespace.ns_name][message](*args)
                for k, v in session.items():
                    namespace.session[k] = v

    def on_message(self, message, handler, **options):
        namespace = options.pop('namespace', '/')
        if namespace not in self.messages:
            self.messages[namespace] = {}
        self.messages[namespace][message] = handler

    def on(self, message, **options):
        def decorator(f):
            self.on_message(message, f, **options)
            return f
        return decorator

    def run(self, app, host=None, port=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = app.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000
        if app.debug:
            @run_with_reloader
            def run_server():
                server = SocketIOServer((host, port), app.wsgi_app, resource='socket.io')
                server.serve_forever()
            run_server()
        else:
            SocketIOServer((host, port), app.wsgi_app, resource='socket.io').serve_forever()


def emit(event, *args, **kwargs):
    return request.namespace.emit(event, *args, **kwargs)


def send(message, json=False, namespace=None, callback=None, broadcast=False):
    return request.namespace.send(message, json, namespace, callback, broadcast)


def error(error_name, error_message, msg_id=None, quiet=False):
    return request.namespace.error(error_name, error_message, msg_id, quiet)


def disconnect(silent=False):
    return request.namespace.disconnect(silent)
