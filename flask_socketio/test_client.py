import uuid

from socketio import packet
from socketio.pubsub_manager import PubSubManager
from werkzeug.test import EnvironBuilder


class SocketIOTestClient(object):
    """
    This class is useful for testing a Flask-SocketIO server. It works in a
    similar way to the Flask Test Client, but adapted to the Socket.IO server.

    :param app: The Flask application instance.
    :param socketio: The application's ``SocketIO`` instance.
    :param namespace: The namespace for the client. If not provided, the client
                      connects to the server on the global namespace.
    :param query_string: A string with custom query string arguments.
    :param headers: A dictionary with custom HTTP headers.
    """
    queue = {}
    ack = None

    def __init__(self, app, socketio, namespace=None, query_string=None,
                 headers=None):
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
        self.queue[self.sid] = []
        self.callback_counter = 0
        self.socketio = socketio
        socketio.server._send_packet = _mock_send_packet
        socketio.server.environ[self.sid] = {}
        if isinstance(socketio.server.manager, PubSubManager):
            raise RuntimeError('Test client cannot be used with a message '
                               'queue. Disable the queue on your test '
                               'configuration.')
        socketio.server.manager.initialize()
        self.connect(namespace=namespace, query_string=query_string,
                     headers=headers)

    def connect(self, namespace=None, query_string=None, headers=None):
        """Connect the client.

        :param namespace: The namespace for the client. If not provided, the
                          client connects to the server on the global
                          namespace.
        :param query_string: A string with custom query string arguments.
        :param headers: A dictionary with custom HTTP headers.

        Note that it is usually not necessary to explicitly call this method,
        since a connection is automatically established when an instance of
        this class is created. An example where it this method would be useful
        is when the application accepts multiple namespace connections.
        """
        url = '/socket.io'
        if query_string:
            if query_string[0] != '?':
                query_string = '?' + query_string
            url += query_string
        environ = EnvironBuilder(url, headers=headers).get_environ()
        environ['flask.app'] = self.app
        self.socketio.server._handle_eio_connect(self.sid, environ)
        if namespace is not None and namespace != '/':
            pkt = packet.Packet(packet.CONNECT, namespace=namespace)
            with self.app.app_context():
                self.socketio.server._handle_eio_message(self.sid,
                                                         pkt.encode())

    def disconnect(self, namespace=None):
        """Disconnect the client.

        :param namespace: The namespace to disconnect. The global namespace is
                         assumed if this argument is not provided.
        """
        pkt = packet.Packet(packet.DISCONNECT, namespace=namespace)
        with self.app.app_context():
            self.socketio.server._handle_eio_message(self.sid, pkt.encode())

    def emit(self, event, *args, **kwargs):
        """Emit an event to the server.

        :param event: The event name.
        :param *args: The event arguments.
        :param callback: ``True`` if the client requests a callback, ``False``
                         if not. Note that client-side callbacks are not
                         implemented, a callback request will just tell the
                         server to provide the arguments to invoke the
                         callback, but no callback is invoked. Instead, the
                         arguments that the server provided for the callback
                         are returned by this function.
        :param namespace: The namespace of the event. The global namespace is
                          assumed if this argument is not provided.
        """
        namespace = kwargs.pop('namespace', None)
        callback = kwargs.pop('callback', False)
        id = None
        if callback:
            self.callback_counter += 1
            id = self.callback_counter
        pkt = packet.Packet(packet.EVENT, data=[event] + list(args),
                            namespace=namespace, id=id)
        self.ack = None
        with self.app.app_context():
            encoded_pkt = pkt.encode()
            if isinstance(encoded_pkt, list):
                for epkt in encoded_pkt:
                    self.socketio.server._handle_eio_message(self.sid, epkt)
            else:
                self.socketio.server._handle_eio_message(self.sid, encoded_pkt)
        if self.ack is not None:
            return self.ack['args'][0] if len(self.ack['args']) == 1 \
                else self.ack['args']

    def send(self, data, json=False, callback=False, namespace=None):
        """Send a text or JSON message to the server.

        :param data: A string, dictionary or list to send to the server.
        :param json: ``True`` to send a JSON message, ``False`` to send a text
                     message.
        :param callback: ``True`` if the client requests a callback, ``False``
                         if not. Note that client-side callbacks are not
                         implemented, a callback request will just tell the
                         server to provide the arguments to invoke the
                         callback, but no callback is invoked. Instead, the
                         arguments that the server provided for the callback
                         are returned by this function.
        :param namespace: The namespace of the event. The global namespace is
                          assumed if this argument is not provided.
        """
        if json:
            msg = 'json'
        else:
            msg = 'message'
        return self.emit(msg, data, callback=callback, namespace=namespace)

    def get_received(self, namespace=None):
        """Return the list of messages received from the server.

        Since this is not a real client, any time the server emits an event,
        the event is simply stored. The test code can invoke this method to
        obtain the list of events that were received since the last call.

        :param namespace: The namespace to get events from. The global
                          namespace is assumed if this argument is not
                          provided.
        """
        namespace = namespace or '/'
        r = [pkt for pkt in self.queue[self.sid]
             if pkt['namespace'] == namespace]
        self.queue[self.sid] = [pkt for pkt in self.queue[self.sid]
                                if pkt not in r]
        return r
