"""
This module contains a collection of auxiliary mock objects used by
unit tests.
"""

import uuid

from socketio import packet
from werkzeug.test import EnvironBuilder


_queue = {}


def _mock_send_packet(sid, pkt):
    global _queue
    if sid not in _queue:
        _queue[sid] = []
    if pkt.packet_type == packet.EVENT or \
            pkt.packet_type == packet.BINARY_EVENT:
        if pkt.data[0] == 'message' or pkt.data[0] == 'json':
            _queue[sid].append({'name': pkt.data[0], 'args': pkt.data[1],
                                'namespace': pkt.namespace or '/'})
        else:
            _queue[sid].append({'name': pkt.data[0], 'args': pkt.data[1:],
                                'namespace': pkt.namespace or '/'})


class SocketIOTestClient(object):
    def __init__(self, app, socketio, namespace=None):
        self.sid = uuid.uuid4().hex
        self.socketio = socketio
        socketio.server._send_packet = _mock_send_packet
        socketio.server.environ[self.sid] = {}
        self.connect(namespace)

    def connect(self, namespace=None):
        environ = EnvironBuilder('/socket.io').get_environ()
        self.socketio.server._handle_eio_connect(self.sid, environ)
        if namespace is not None and namespace != '/':
            pkt = packet.Packet(packet.CONNECT, namespace=namespace)
            self.socketio.server._handle_eio_message(self.sid, pkt.encode())

    def disconnect(self, namespace=None):
        pkt = packet.Packet(packet.DISCONNECT, namespace=namespace)
        self.socketio.server._handle_eio_message(self.sid, pkt.encode())

    def emit(self, event, *args, **kwargs):
        namespace = kwargs.pop('namespace', None)
        pkt = packet.Packet(packet.EVENT, data=[event] + list(args),
                            namespace=namespace, binary=False)
        self.socketio.server._handle_eio_message(self.sid, pkt.encode())

    def send(self, data, json=False, namespace=None):
        if json:
            msg = 'json'
        else:
            msg = 'message'
        return self.emit(msg, data, namespace=namespace)

    def get_received(self, namespace=None):
        if self.sid not in _queue:
            return []
        namespace = namespace or '/'
        r = [pkt for pkt in _queue[self.sid] if pkt['namespace'] == namespace]
        _queue[self.sid] = [pkt for pkt in _queue[self.sid] if pkt not in r]
        return r