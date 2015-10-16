import uuid

from socketio import packet
from werkzeug.test import EnvironBuilder


class SocketIOTestClient(object):
    """Fake client useful for testing of a Flask-SocketIO server."""
    queue = {}
    ack = None

    def __init__(self, app, socketio, namespace=None):
        def _mock_send_packet(sid, pkt):
            if pkt.packet_type == packet.EVENT or \
                    pkt.packet_type == packet.BINARY_EVENT:
                if sid not in self.queue:
                    self.queue[sid] = []
                if pkt.data[0] == 'message' or pkt.data[0] == 'json':
                    self.queue[sid].append({'name': pkt.data[0],
                                            'args': pkt.data[1],
                                            'namespace': pkt.namespace or '/'})
                else:
                    self.queue[sid].append({'name': pkt.data[0],
                                            'args': pkt.data[1:],
                                            'namespace': pkt.namespace or '/'})
            elif pkt.packet_type == packet.ACK or \
                    pkt.packet_type == packet.BINARY_ACK:
                self.ack = {'args': pkt.data,
                            'namespace': pkt.namespace or '/'}

        self.app = app
        self.sid = uuid.uuid4().hex
        self.callback_counter = 0
        self.socketio = socketio
        socketio.server._send_packet = _mock_send_packet
        socketio.server.environ[self.sid] = {}
        self.connect(namespace)

    def connect(self, namespace=None):
        """Connect the client."""
        environ = EnvironBuilder('/socket.io').get_environ()
        environ['flask.app'] = self.app
        self.socketio.server._handle_eio_connect(self.sid, environ)
        if namespace is not None and namespace != '/':
            pkt = packet.Packet(packet.CONNECT, namespace=namespace)
            with self.app.app_context():
                self.socketio.server._handle_eio_message(self.sid,
                                                         pkt.encode())

    def disconnect(self, namespace=None):
        """Disconnect the client."""
        pkt = packet.Packet(packet.DISCONNECT, namespace=namespace)
        with self.app.app_context():
            self.socketio.server._handle_eio_message(self.sid, pkt.encode())

    def emit(self, event, *args, **kwargs):
        """Emit an event to the server."""
        namespace = kwargs.pop('namespace', None)
        callback = kwargs.pop('callback', False)
        id = None
        if callback:
            self.callback_counter += 1
            id = self.callback_counter
        pkt = packet.Packet(packet.EVENT, data=[event] + list(args),
                            namespace=namespace, id=id, binary=False)
        self.ack = None
        with self.app.app_context():
            self.socketio.server._handle_eio_message(self.sid, pkt.encode())
        if self.ack is not None:
            return self.ack['args'][0] if len(self.ack['args']) == 1 \
                else self.ack['args']

    def send(self, data, json=False, callback=False, namespace=None):
        """Send a message to the server."""
        if json:
            msg = 'json'
        else:
            msg = 'message'
        return self.emit(msg, data, callback=callback, namespace=namespace)

    def get_received(self, namespace=None):
        """Return the list of messages received from the server."""
        namespace = namespace or '/'
        r = [pkt for pkt in self.queue[self.sid]
             if pkt['namespace'] == namespace]
        self.queue[self.sid] = [pkt for pkt in self.queue[self.sid]
                                if pkt not in r]
        return r
