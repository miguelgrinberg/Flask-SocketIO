from socketio.packet import decode
from flask.testing import make_test_environ_builder

def event_packet(event, namespace='/', args=None):
    return {
        'type': 'event',
        'endpoint': namespace,
        'name': event,
        'args': args
    }

def message_packet(message, namespace='/'):
        return {
            'type': 'message',
            'endpoint': namespace,
            'data': message
        }

class SocketIOClient(object):
    def __init__(self, application, namespaces):
        self.socket = self._socket(application, namespaces)
        self.packets = []

    def _socket(self, application, namespaces_):
        builder = make_test_environ_builder(application, path='/socket.io/')
        environ = builder.get_environ()
        class BlockingSocket(object):
            client = self
            request = application
            namespaces = namespaces_
            active_ns = {}
            def __init__(self):
                environ['socketio'] = self
                self.environ = environ
                self.session = {}

            def receive(self, pkt):
                endpoint = pkt['endpoint']
                # This is a log message in virtsocket
                assert endpoint in self.namespaces

                if endpoint in self.active_ns:
                    pkt_ns = self.active_ns[endpoint]
                else:
                    new_ns_class = self.namespaces[endpoint]
                    pkt_ns = new_ns_class(self.environ, endpoint, self.request)
                    for cls in type(pkt_ns).__mro__:
                        if hasattr(cls, 'initialize'):
                            cls.initialize(pkt_ns)

                    self.active_ns[endpoint] = pkt_ns

                    pkt_ns.process_packet(pkt)
                    #TODO: handle ack callbacks

            def send_packet(self, pkt):
                self.client.packets.append(pkt)
                
        return BlockingSocket()

    def send(self, message, namespace='/'):
        self.socket.receive(message_packet(message, namespace))

    def emit(self, event, namespace='/', args=None):
        if not args:
            args = []
        self.socket.receive(event_packet(event, namespace, args))
