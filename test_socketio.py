import unittest
import coverage

cov = coverage.coverage()
cov.start()

from flask import Flask
from flask.ext.socketio import SocketIO, send, emit

app = Flask(__name__)
socketio = SocketIO(app)
disconnected = None

@socketio.on('connect')
def on_connect():
    send('connected')

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
    disconnected = 'test'

@socketio.on('message')
def on_message(message):
    send(message)

@socketio.on('message', namespace='/test')
def on_message_test(message):
    send(message, json=True)


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
        client.disconnect('/test')

if __name__ == '__main__':
    unittest.main()
