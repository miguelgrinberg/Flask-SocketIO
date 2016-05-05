import unittest
import coverage

cov = coverage.coverage()
cov.start()

from flask import Flask, session, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)
disconnected = None


@socketio.on('connect')
def on_connect():
    send('connected')


@socketio.on('disconnect')
def on_disconnect():
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
    if message == 'test session':
        session['a'] = 'b'
    if message not in "test noack":
        return message


@socketio.on('json')
def on_json(data):
    send(data, json=True, broadcast=True)
    if not data.get('noack'):
        return data


@socketio.on('message', namespace='/test')
def on_message_test(message):
    send(message)


@socketio.on('json', namespace='/test')
def on_json_test(data):
    send(data, json=True, namespace='/test')


@socketio.on('my custom event')
def on_custom_event(data):
    emit('my custom response', data)
    if not data.get('noack'):
        return data


@socketio.on('other custom event')
def get_request_event(data):
    global request_event_data
    request_event_data = request.event
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


@socketio.on('join room')
def on_join_room(data):
    join_room(data['room'])


@socketio.on('leave room')
def on_leave_room(data):
    leave_room(data['room'])


@socketio.on('join room', namespace='/test')
def on_join_room_namespace(data):
    join_room(data['room'])


@socketio.on('leave room', namespace='/test')
def on_leave_room_namespace(data):
    leave_room(data['room'])


@socketio.on('my room event')
def on_room_event(data):
    room = data.pop('room')
    emit('my room response', data, room=room)


@socketio.on('my room namespace event', namespace='/test')
def on_room_namespace_event(data):
    room = data.pop('room')
    send('room message', room=room)


@socketio.on_error()
def error_handler(value):
    if isinstance(value, AssertionError):
        global error_testing
        error_testing = True
    else:
        raise value
    return value


@socketio.on('error testing')
def raise_error(data):
    raise AssertionError()


@socketio.on_error('/test')
def error_handler_namespace(value):
    if isinstance(value, AssertionError):
        global error_testing_namespace
        error_testing_namespace = True
    else:
        raise value
    return value


@socketio.on("error testing", namespace='/test')
def raise_error_namespace(data):
    raise AssertionError()


@socketio.on_error_default
def error_handler_default(value):
    if isinstance(value, AssertionError):
        global error_testing_default
        error_testing_default = True
    else:
        raise value
    return value


@socketio.on("error testing", namespace='/unused_namespace')
def raise_error_default(data):
    raise AssertionError()


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
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args'], 'connected')
        client.disconnect()

    def test_connect_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        received = client.get_received('/test')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args'], 'connected-test')
        client.disconnect(namespace='/test')

    def test_disconnect(self):
        global disconnected
        disconnected = None
        client = socketio.test_client(app)
        client.disconnect()
        self.assertEqual(disconnected, '/')

    def test_disconnect_namespace(self):
        global disconnected
        disconnected = None
        client = socketio.test_client(app, namespace='/test')
        client.disconnect('/test')
        self.assertEqual(disconnected, '/test')

    def test_send(self):
        client = socketio.test_client(app)
        client.get_received()
        client.send('echo this message back')
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args'], 'echo this message back')

    def test_send_json(self):
        client1 = socketio.test_client(app)
        client2 = socketio.test_client(app)
        client1.get_received()
        client2.get_received()
        client1.send({'a': 'b'}, json=True)
        received = client1.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args']['a'], 'b')
        received = client2.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args']['a'], 'b')

    def test_send_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')
        client.send('echo this message back', namespace='/test')
        received = client.get_received('/test')
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args'] == 'echo this message back')

    def test_send_json_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')
        client.send({'a': 'b'}, json=True, namespace='/test')
        received = client.get_received('/test')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args']['a'], 'b')

    def test_emit(self):
        client = socketio.test_client(app)
        client.get_received()
        client.emit('my custom event', {'a': 'b'})
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')

    def test_request_event_data(self):
        client = socketio.test_client(app)
        client.get_received()
        global request_event_data
        request_event_data = None
        client.emit('other custom event', 'foo')
        expected_data = {'message': 'other custom event', 'args': ('foo',)}
        self.assertEqual(request_event_data, expected_data)

    def test_emit_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')
        client.emit('my custom namespace event', {'a': 'b'}, namespace='/test')
        received = client.get_received('/test')
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom namespace response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')

    def test_broadcast(self):
        client1 = socketio.test_client(app)
        client2 = socketio.test_client(app)
        client3 = socketio.test_client(app, namespace='/test')
        client2.get_received()
        client3.get_received('/test')
        client1.emit('my custom broadcast event', {'a': 'b'}, broadcast=True)
        received = client2.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')
        self.assertEqual(len(client3.get_received('/test')), 0)

    def test_broadcast_namespace(self):
        client1 = socketio.test_client(app, namespace='/test')
        client2 = socketio.test_client(app, namespace='/test')
        client3 = socketio.test_client(app)
        client2.get_received('/test')
        client3.get_received()
        client1.emit('my custom broadcast namespace event', {'a': 'b'},
                     namespace='/test')
        received = client2.get_received('/test')
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom namespace response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')
        self.assertEqual(len(client3.get_received()), 0)

    def test_session(self):
        client = socketio.test_client(app)
        client.get_received()
        client.send('echo this message back')
        self.assertNotIn('saved_session', socketio.server.environ[client.sid])
        client.send('test session')
        session = socketio.server.environ[client.sid]['saved_session']
        self.assertEqual(session['a'], 'b')

    def test_room(self):
        client1 = socketio.test_client(app)
        client2 = socketio.test_client(app)
        client3 = socketio.test_client(app, namespace='/test')
        client1.get_received()
        client2.get_received()
        client3.get_received('/test')
        client1.emit('join room', {'room': 'one'})
        client2.emit('join room', {'room': 'one'})
        client3.emit('join room', {'room': 'one'}, namespace='/test')
        client1.emit('my room event', {'a': 'b', 'room': 'one'})
        received = client1.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my room response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')
        self.assertEqual(received, client2.get_received())
        received = client3.get_received('/test')
        self.assertEqual(len(received), 0)
        client1.emit('leave room', {'room': 'one'})
        client1.emit('my room event', {'a': 'b', 'room': 'one'})
        received = client1.get_received()
        self.assertEqual(len(received), 0)
        received = client2.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my room response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')
        client2.disconnect()
        socketio.emit('my room event', {'a': 'b'}, room='one')
        received = client1.get_received()
        self.assertEqual(len(received), 0)
        received = client3.get_received('/test')
        self.assertEqual(len(received), 0)
        client3.emit('my room namespace event', {'room': 'one'},
                     namespace='/test')
        received = client3.get_received('/test')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'message')
        self.assertEqual(received[0]['args'], 'room message')
        socketio.close_room('one', namespace='/test')
        client3.emit('my room namespace event', {'room': 'one'},
                     namespace='/test')
        received = client3.get_received('/test')
        self.assertEqual(len(received), 0)

    def test_error_handling(self):
        client = socketio.test_client(app)
        client.get_received()
        global error_testing
        error_testing = False
        client.emit("error testing", "")
        self.assertTrue(error_testing)

    def test_error_handling_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')
        global error_testing_namespace
        error_testing_namespace = False
        client.emit("error testing", "", namespace='/test')
        self.assertTrue(error_testing_namespace)

    def test_error_handling_default(self):
        client = socketio.test_client(app, namespace='/unused_namespace')
        client.get_received('/unused_namespace')
        global error_testing_default
        error_testing_default = False
        client.emit("error testing", "", namespace='/unused_namespace')
        self.assertTrue(error_testing_default)

    def test_ack(self):
        client1 = socketio.test_client(app)
        ack = client1.send('echo this message back', callback=True)
        self.assertEqual(ack, 'echo this message back')
        client2 = socketio.test_client(app)
        ack2 = client2.send({'a': 'b'}, json=True, callback=True)
        self.assertEqual(ack2, {'a': 'b'})
        client3 = socketio.test_client(app)
        ack3 = client3.emit('my custom event', {'a': 'b'}, callback=True)
        self.assertEqual(ack3, {'a': 'b'})

    def test_noack(self):
        client1 = socketio.test_client(app)
        no_ack_dict = {'noack': True}
        noack = client1.send("test noack", callback=True)
        self.assertIsNone(noack)
        client2 = socketio.test_client(app)
        noack2 = client2.send(no_ack_dict, json=True, callback=True)
        client3 = socketio.test_client(app)
        self.assertIsNone(noack2)
        noack3 = client3.emit('my custom event', no_ack_dict)
        self.assertIsNone(noack3)

    def test_error_handling_ack(self):
        client1 = socketio.test_client(app)
        errorack = client1.emit("error testing", "", callback=True)
        self.assertIsNotNone(errorack)
        client2 = socketio.test_client(app, namespace='/test')
        errorack_namespace = client2.emit("error testing", "",
                                          namespace='/test', callback=True)
        self.assertIsNotNone(errorack_namespace)
        client3 = socketio.test_client(app, namespace='/unused_namespace')
        errorack_default = client3.emit("error testing", "",
                                        namespace='/unused_namespace',
                                        callback=True)
        self.assertIsNotNone(errorack_default)

if __name__ == '__main__':
    unittest.main()
