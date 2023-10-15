import json
import time
import unittest

from flask import Flask, session, request, json as flask_json
from flask_socketio import SocketIO, send, emit, join_room, leave_room, \
    Namespace, disconnect, ConnectionRefusedError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)
disconnected = None


@socketio.on('connect')
def on_connect(auth):
    if auth != {'foo': 'bar'}:  # pragma: no cover
        return False
    if request.args.get('fail'):
        raise ConnectionRefusedError('failed!')
    send('connected')
    send(json.dumps(request.args.to_dict(flat=False)))
    send(json.dumps({h: request.headers[h] for h in request.headers.keys()
                     if h not in ['Host', 'Content-Type', 'Content-Length']}))
    emit('dummy', to='nobody')


@socketio.on('disconnect')
def on_disconnect():
    global disconnected
    disconnected = '/'


@socketio.event(namespace='/test')
def connect():
    send('connected-test')
    send(json.dumps(request.args.to_dict(flat=False)))
    send(json.dumps({h: request.headers[h] for h in request.headers.keys()
                     if h not in ['Host', 'Content-Type', 'Content-Length']}))


@socketio.on('disconnect', namespace='/test')
def on_disconnect_test():
    global disconnected
    disconnected = '/test'


@socketio.on('connect', namespace='/bgtest')
def on_bgtest_connect():
    def background_task():
        socketio.emit('bgtest', namespace='/bgtest')

    socketio.start_background_task(background_task)


@socketio.event
def message(message):
    send(message)
    if message == 'test session':
        if not socketio.manage_session and 'a' in session:
            raise RuntimeError('session is being stored')
        if 'a' not in session:
            session['a'] = 'b'
        else:
            session['a'] = 'c'
    if message not in "test noackargs":
        return message


@socketio.on('json')
def on_json(data):
    send(data, json=True, broadcast=True)
    if not data.get('noackargs'):
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
    if not data.get('noackargs'):
        return data


@socketio.on('other custom event')
@socketio.on('and another custom event')
def get_request_event(data):
    global request_event_data
    request_event_data = request.event
    emit('my custom response', data)


def get_request_event2(data):
    global request_event_data
    request_event_data = request.event
    emit('my custom response', data)


socketio.on_event('yet another custom event', get_request_event2)


@socketio.on('my custom namespace event', namespace='/test')
def on_custom_event_test(data):
    emit('my custom namespace response', data, namespace='/test')


def on_custom_event_test2(data):
    emit('my custom namespace response', data, namespace='/test')


socketio.on_event('yet another custom namespace event', on_custom_event_test2,
                  namespace='/test')


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


@socketio.on('bad response')
def on_bad_response():
    emit('my custom response', {'foo': socketio})


@socketio.on('bad callback')
def on_bad_callback():
    return {'foo': socketio}


@socketio.on('changing response')
def on_changing_response():
    data = {'foo': 'bar'}
    emit('my custom response', data)
    data['foo'] = 'baz'
    return data


@socketio.on_error()
def error_handler(value):
    if isinstance(value, AssertionError):
        global error_testing
        error_testing = True
    else:
        raise value
    return 'error'


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
    return 'error/test'


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
    return 'error/default'


@socketio.on("error testing", namespace='/unused_namespace')
def raise_error_default(data):
    raise AssertionError()


class MyNamespace(Namespace):
    def on_connect(self):
        send('connected-ns')
        send(json.dumps(request.args.to_dict(flat=False)))
        send(json.dumps(
            {h: request.headers[h] for h in request.headers.keys()
             if h not in ['Host', 'Content-Type', 'Content-Length']}))

    def on_disconnect(self):
        global disconnected
        disconnected = '/ns'

    def on_message(self, message):
        send(message)
        if message == 'test session':
            session['a'] = 'b'
        if message not in "test noackargs":
            return message

    def on_json(self, data):
        send(data, json=True, broadcast=True)
        if not data.get('noackargs'):
            return data

    def on_exit(self, data):
        disconnect()

    def on_my_custom_event(self, data):
        emit('my custom response', data)
        if not data.get('noackargs'):
            return data

    def on_other_custom_event(self, data):
        global request_event_data
        request_event_data = request.event
        emit('my custom response', data)


socketio.on_namespace(MyNamespace('/ns'))


@app.route('/session')
def session_route():
    session['foo'] = 'bar'
    return ''


class TestSocketIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_connect(self):
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client2 = socketio.test_client(app, auth={'foo': 'bar'})
        self.assertTrue(client.is_connected())
        self.assertTrue(client2.is_connected())
        self.assertNotEqual(client.eio_sid, client2.eio_sid)
        received = client.get_received()
        self.assertEqual(len(received), 3)
        self.assertEqual(received[0]['args'], 'connected')
        self.assertEqual(received[1]['args'], '{}')
        self.assertEqual(received[2]['args'], '{}')
        client.disconnect()
        self.assertFalse(client.is_connected())
        self.assertTrue(client2.is_connected())
        client2.disconnect()
        self.assertFalse(client2.is_connected())

    def test_connect_query_string_and_headers(self):
        client = socketio.test_client(
            app, query_string='?foo=bar&foo=baz',
            headers={'Authorization': 'Bearer foobar'},
            auth={'foo': 'bar'})
        received = client.get_received()
        self.assertEqual(len(received), 3)
        self.assertEqual(received[0]['args'], 'connected')
        self.assertEqual(received[1]['args'], '{"foo": ["bar", "baz"]}')
        self.assertEqual(received[2]['args'],
                         '{"Authorization": "Bearer foobar"}')
        client.disconnect()

    def test_connect_namespace(self):
        client = socketio.test_client(app, namespace='/test')
        self.assertTrue(client.is_connected('/test'))
        received = client.get_received('/test')
        self.assertEqual(len(received), 3)
        self.assertEqual(received[0]['args'], 'connected-test')
        self.assertEqual(received[1]['args'], '{}')
        self.assertEqual(received[2]['args'], '{}')
        client.disconnect(namespace='/test')
        self.assertFalse(client.is_connected('/test'))

    def test_connect_namespace_query_string_and_headers(self):
        client = socketio.test_client(
            app, namespace='/test', query_string='foo=bar',
            headers={'My-Custom-Header': 'Value'})
        received = client.get_received('/test')
        self.assertEqual(len(received), 3)
        self.assertEqual(received[0]['args'], 'connected-test')
        self.assertEqual(received[1]['args'], '{"foo": ["bar"]}')
        self.assertEqual(received[2]['args'], '{"My-Custom-Header": "Value"}')
        client.disconnect(namespace='/test')

    def test_connect_rejected(self):
        client = socketio.test_client(app, query_string='fail=1',
                                      auth={'foo': 'bar'})
        self.assertFalse(client.is_connected())

    def test_disconnect(self):
        global disconnected
        disconnected = None
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client.disconnect()
        self.assertEqual(disconnected, '/')

    def test_disconnect_namespace(self):
        global disconnected
        disconnected = None
        client = socketio.test_client(app, namespace='/test')
        client.disconnect('/test')
        self.assertEqual(disconnected, '/test')

    def test_message_queue_options(self):
        app = Flask(__name__)
        socketio = SocketIO(app, message_queue='redis://')
        self.assertFalse(socketio.server_options['client_manager'].write_only)

        app = Flask(__name__)
        socketio = SocketIO(app)
        socketio.init_app(app, message_queue='redis://')
        self.assertFalse(socketio.server_options['client_manager'].write_only)

        app = Flask(__name__)
        socketio = SocketIO(message_queue='redis://')
        self.assertTrue(socketio.server_options['client_manager'].write_only)

        app = Flask(__name__)
        socketio = SocketIO()
        socketio.init_app(None, message_queue='redis://')
        self.assertTrue(socketio.server_options['client_manager'].write_only)

    def test_send(self):
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client.get_received()
        client.send('echo this message back')
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args'], 'echo this message back')

    def test_send_json(self):
        client1 = socketio.test_client(app, auth={'foo': 'bar'})
        client2 = socketio.test_client(app, auth={'foo': 'bar'})
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
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client.get_received()
        client.emit('my custom event', {'a': 'b'})
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')

    def test_emit_binary(self):
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client.get_received()
        client.emit('my custom event', {u'a': b'\x01\x02\x03'})
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom response')
        self.assertEqual(received[0]['args'][0]['a'], b'\x01\x02\x03')

    def test_request_event_data(self):
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client.get_received()
        global request_event_data
        request_event_data = None
        client.emit('other custom event', 'foo')
        expected_data = {'message': 'other custom event', 'args': ('foo',)}
        self.assertEqual(request_event_data, expected_data)
        client.emit('and another custom event', 'bar')
        expected_data = {'message': 'and another custom event',
                         'args': ('bar',)}
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
        client1 = socketio.test_client(app, auth={'foo': 'bar'})
        client2 = socketio.test_client(app, auth={'foo': 'bar'})
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
        client3 = socketio.test_client(app, auth={'foo': 'bar'})
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

    def test_managed_session(self):
        flask_client = app.test_client()
        flask_client.get('/session')
        client = socketio.test_client(app, flask_test_client=flask_client,
                                      auth={'foo': 'bar'})
        client.get_received()
        client.send('echo this message back')
        self.assertEqual(
            socketio.server.environ[client.eio_sid]['saved_session'],
            {'foo': 'bar'})
        client.send('test session')
        self.assertEqual(
            socketio.server.environ[client.eio_sid]['saved_session'],
            {'a': 'b', 'foo': 'bar'})
        client.send('test session')
        self.assertEqual(
            socketio.server.environ[client.eio_sid]['saved_session'],
            {'a': 'c', 'foo': 'bar'})

    def test_unmanaged_session(self):
        socketio.manage_session = False
        flask_client = app.test_client()
        flask_client.get('/session')
        client = socketio.test_client(app, flask_test_client=flask_client,
                                      auth={'foo': 'bar'})
        client.get_received()
        client.send('test session')
        client.send('test session')
        socketio.manage_session = True

    def test_room(self):
        client1 = socketio.test_client(app, auth={'foo': 'bar'})
        client2 = socketio.test_client(app, auth={'foo': 'bar'})
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
        client = socketio.test_client(app, auth={'foo': 'bar'})
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
        client1 = socketio.test_client(app, auth={'foo': 'bar'})
        client2 = socketio.test_client(app, auth={'foo': 'bar'})
        client3 = socketio.test_client(app, auth={'foo': 'bar'})
        ack = client1.send('echo this message back', callback=True)
        self.assertEqual(ack, 'echo this message back')
        ack = client1.send('test noackargs', callback=True)
        # python-socketio releases before 1.5 did not correctly implement
        # callbacks with no arguments. Here we check for [] (the correct, 1.5
        # and up response) and None (the wrong pre-1.5 response).
        self.assertTrue(ack == [] or ack is None)
        ack2 = client2.send({'a': 'b'}, json=True, callback=True)
        self.assertEqual(ack2, {'a': 'b'})
        ack3 = client3.emit('my custom event', {'a': 'b'}, callback=True)
        self.assertEqual(ack3, {'a': 'b'})

    def test_noack(self):
        client1 = socketio.test_client(app, auth={'foo': 'bar'})
        client2 = socketio.test_client(app, auth={'foo': 'bar'})
        client3 = socketio.test_client(app, auth={'foo': 'bar'})
        no_ack_dict = {'noackargs': True}
        noack = client1.send("test noackargs", callback=False)
        self.assertIsNone(noack)
        noack2 = client2.send(no_ack_dict, json=True, callback=False)
        self.assertIsNone(noack2)
        noack3 = client3.emit('my custom event', no_ack_dict)
        self.assertIsNone(noack3)

    def test_error_handling_ack(self):
        client1 = socketio.test_client(app, auth={'foo': 'bar'})
        client2 = socketio.test_client(app, namespace='/test')
        client3 = socketio.test_client(app, namespace='/unused_namespace')
        errorack = client1.emit("error testing", "", callback=True)
        self.assertEqual(errorack, 'error')
        errorack_namespace = client2.emit("error testing", "",
                                          namespace='/test', callback=True)
        self.assertEqual(errorack_namespace, 'error/test')
        errorack_default = client3.emit("error testing", "",
                                        namespace='/unused_namespace',
                                        callback=True)
        self.assertEqual(errorack_default, 'error/default')

    def test_on_event(self):
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client.get_received()
        global request_event_data
        request_event_data = None
        client.emit('yet another custom event', 'foo')
        expected_data = {'message': 'yet another custom event',
                         'args': ('foo',)}
        self.assertEqual(request_event_data, expected_data)

        client = socketio.test_client(app, namespace='/test')
        client.get_received('/test')
        client.emit('yet another custom namespace event', {'a': 'b'},
                    namespace='/test')
        received = client.get_received('/test')
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom namespace response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')

    def test_connect_class_based(self):
        client = socketio.test_client(app, namespace='/ns')
        received = client.get_received('/ns')
        self.assertEqual(len(received), 3)
        self.assertEqual(received[0]['args'], 'connected-ns')
        self.assertEqual(received[1]['args'], '{}')
        self.assertEqual(received[2]['args'], '{}')
        client.disconnect('/ns')

    def test_connect_class_based_query_string_and_headers(self):
        client = socketio.test_client(
            app, namespace='/ns', query_string='foo=bar',
            headers={'Authorization': 'Basic foobar'})
        received = client.get_received('/ns')
        self.assertEqual(len(received), 3)
        self.assertEqual(received[0]['args'], 'connected-ns')
        self.assertEqual(received[1]['args'], '{"foo": ["bar"]}')
        self.assertEqual(received[2]['args'],
                         '{"Authorization": "Basic foobar"}')
        client.disconnect('/ns')

    def test_disconnect_class_based(self):
        global disconnected
        disconnected = None
        client = socketio.test_client(app, namespace='/ns')
        client.disconnect('/ns')
        self.assertEqual(disconnected, '/ns')

    def test_send_class_based(self):
        client = socketio.test_client(app, namespace='/ns')
        client.get_received('/ns')
        client.send('echo this message back', namespace='/ns')
        received = client.get_received('/ns')
        self.assertTrue(len(received) == 1)
        self.assertTrue(received[0]['args'] == 'echo this message back')

    def test_send_json_class_based(self):
        client = socketio.test_client(app, namespace='/ns')
        client.get_received('/ns')
        client.send({'a': 'b'}, json=True, namespace='/ns')
        received = client.get_received('/ns')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args']['a'], 'b')

    def test_server_disconnected(self):
        client = socketio.test_client(app, namespace='/ns')
        client2 = socketio.test_client(app, namespace='/ns')
        client.get_received('/ns')
        client2.get_received('/ns')
        client.emit('exit', {}, namespace='/ns')
        self.assertFalse(client.is_connected('/ns'))
        self.assertTrue(client2.is_connected('/ns'))
        with self.assertRaises(RuntimeError):
            client.emit('hello', {}, namespace='/ns')
        client2.emit('exit', {}, namespace='/ns')
        self.assertFalse(client2.is_connected('/ns'))
        with self.assertRaises(RuntimeError):
            client2.emit('hello', {}, namespace='/ns')

    def test_emit_class_based(self):
        client = socketio.test_client(app, namespace='/ns')
        client.get_received('/ns')
        client.emit('my_custom_event', {'a': 'b'}, namespace='/ns')
        received = client.get_received('/ns')
        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]['args']), 1)
        self.assertEqual(received[0]['name'], 'my custom response')
        self.assertEqual(received[0]['args'][0]['a'], 'b')

    def test_request_event_data_class_based(self):
        client = socketio.test_client(app, namespace='/ns')
        client.get_received('/ns')
        global request_event_data
        request_event_data = None
        client.emit('other_custom_event', 'foo', namespace='/ns')
        expected_data = {'message': 'other_custom_event', 'args': ('foo',)}
        self.assertEqual(request_event_data, expected_data)

    def test_delayed_init(self):
        app = Flask(__name__)
        socketio = SocketIO(allow_upgrades=False, json=flask_json)

        @socketio.on('connect')
        def on_connect():
            send({'connected': 'foo'}, json=True)

        socketio.init_app(app, cookie='foo')
        self.assertFalse(socketio.server.eio.allow_upgrades)
        self.assertEqual(socketio.server.eio.cookie, 'foo')

        client = socketio.test_client(app, auth={'foo': 'bar'})
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args'], {'connected': 'foo'})

    def test_encode_decode(self):
        client = socketio.test_client(app, auth={'foo': 'bar'})
        client.get_received()
        data = {'foo': 'bar', 'invalid': socketio}
        self.assertRaises(TypeError, client.emit, 'my custom event', data,
                          callback=True)
        data = {'foo': 'bar'}
        ack = client.emit('my custom event', data, callback=True)
        data['foo'] = 'baz'
        received = client.get_received()
        self.assertEqual(ack, {'foo': 'bar'})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args'][0], {'foo': 'bar'})

    def test_encode_decode_2(self):
        client = socketio.test_client(app, auth={'foo': 'bar'})
        self.assertRaises(TypeError, client.emit, 'bad response')
        self.assertRaises(TypeError, client.emit, 'bad callback',
                          callback=True)
        client.get_received()
        ack = client.emit('changing response', callback=True)
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['args'][0], {'foo': 'bar'})
        self.assertEqual(ack, {'foo': 'baz'})

    def test_background_task(self):
        client = socketio.test_client(app, namespace='/bgtest')
        self.assertTrue(client.is_connected(namespace='/bgtest'))
        time.sleep(0.1)
        received = client.get_received('/bgtest')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'bgtest')


if __name__ == '__main__':
    unittest.main()
