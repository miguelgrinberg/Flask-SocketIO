import unittest
import coverage

cov = coverage.coverage()
cov.start()

from flask import Flask, session
from flask.ext.socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)
disconnected = None

@socketio.on('connect')
def on_connect():
    send('connected')
    session['a'] = 'b'

@socketio.on('disconnect')
def on_connect():
    global disconnected
    disconnected = '/'

@socketio.on('connect', namespace='/test')
def on_connect_test():
    send('connected-test')

@socketio.on('disconnect', namespace='/test')
def on_disconnect_test():
    global disconnected
    disconnected = '/test'

@socketio.on('message')
def on_message(message):
    send(message)

@socketio.on('json')
def on_json(data):
    send(data, json=True, broadcast=True)

@socketio.on('message', namespace='/test')
def on_message_test(message):
    send(message)

@socketio.on('json', namespace='/test')
def on_json_test(data):
    send(data, json=True, namespace='/test')

@socketio.on('my custom event')
def on_custom_event(data):
    emit('my custom response', data)

@socketio.on('my custom namespace event', namespace='/test')
def on_custom_event_test(data):
    emit('my custom namespace response', data, namespace='/test')

@socketio.on('my custom broadcast event')
def on_custom_event_broadcast(data):
    emit('my custom response', data, broadcast=True)

@socketio.on('my custom broadcast namespace event', namespace='/test')
def on_custom_event_broadcast_test(data):
    emit('my custom namespace response', data, namespace='/test',
         broadcast=True)


class TestSocketIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        cov.stop()
        cov.report(include='flask_socketio/__init__.py')

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_connect(self):
        client = socketio.test_client(app)
        received = client.get_received()
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args'] == 'connected')
        client.disconnect()

    def test_connect_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        received = client.get_received('/test')
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args'] == 'connected-test')
        client.disconnect(namespace='/test')

    def test_disconnect(self):
        global disconnected
        disconnected = None
        client = socketio.test_client(app)
        client.disconnect()
        self.assertTrue(disconnected == '/')

    def test_disconnect_namespace(self):
        global disconnected
        disconnected = None
        client = socketio.test_client(app, namespace='/test')
        client.disconnect('/test')
        self.assertTrue(disconnected == '/test')

    def test_send(self):
        client = socketio.test_client(app)
        client.get_received()  # clean received
        client.send('echo this message back')
        received = client.get_received()
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args'] == 'echo this message back')

    def test_send_json(self):
        client1 = socketio.test_client(app)
        client2 = socketio.test_client(app)
        client1.get_received()  # clean received
        client2.get_received()  # clean received
        client1.send({'a': 'b'}, json=True)
        received = client1.get_received()
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args']['a'] == 'b')
        received = client2.get_received()
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args']['a'] == 'b')

    def test_send_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')  # clean received
        client.send('echo this message back', namespace='/test')
        received = client.get_received('/test')
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args'] == 'echo this message back')

    def test_send_json_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')  # clean received
        client.send({'a': 'b'}, json=True, namespace='/test')
        received = client.get_received('/test')
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args']['a'] == 'b')

    def test_emit(self):
        client = socketio.test_client(app)
        client.get_received()  # clean received
        client.emit('my custom event', {'a': 'b'})
        received = client.get_received()
        self.assertTrue(len(received) == 1)
        self.assertTrue(len(received[0]['args']) == 1)
        self.assertTrue(received[0]['name'] == 'my custom response')
        self.assertTrue(received[0]['args'][0]['a'] == 'b')

    def test_emit_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')  # clean received
        client.emit('my custom namespace event', {'a': 'b'}, namespace='/test')
        received = client.get_received('/test')
        self.assertTrue(len(received) == 1)
        self.assertTrue(len(received[0]['args']) == 1)
        self.assertTrue(received[0]['name'] == 'my custom namespace response')
        self.assertTrue(received[0]['args'][0]['a'] == 'b')

    def test_broadcast(self):
        client1 = socketio.test_client(app)
        client2 = socketio.test_client(app)
        client3 = socketio.test_client(app, namespace='/test')
        client2.get_received()  # clean
        client3.get_received('/test')  # clean
        client1.emit('my custom broadcast event', {'a': 'b'}, broadcast=True)
        received = client2.get_received()
        self.assertTrue(len(received) == 1)
        self.assertTrue(len(received[0]['args']) == 1)
        self.assertTrue(received[0]['name'] == 'my custom response')
        self.assertTrue(received[0]['args'][0]['a'] == 'b')
        self.assertTrue(len(client3.get_received('/test')) == 0)

    def test_broadcast_namespace(self):
        client1 = socketio.test_client(app, namespace='/test')
        client2 = socketio.test_client(app, namespace='/test')
        client3 = socketio.test_client(app)
        client2.get_received('/test')  # clean
        client3.get_received()  # clean
        client1.emit('my custom broadcast namespace event', {'a': 'b'},
                     namespace='/test', broadcast=True)
        received = client2.get_received('/test')
        self.assertTrue(len(received) == 1)
        self.assertTrue(len(received[0]['args']) == 1)
        self.assertTrue(received[0]['name'] == 'my custom namespace response')
        self.assertTrue(received[0]['args'][0]['a'] == 'b')
        self.assertTrue(len(client3.get_received()) == 0)

    def test_session(self):
        client = socketio.test_client(app)
        client.get_received()  # clean received
        client.send('echo this message back')
        self.assertTrue(client.socket.namespace[''].session['a'] == 'b')

if __name__ == '__main__':
    unittest.main()
