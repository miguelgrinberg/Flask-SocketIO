.. Flask-SocketIO documentation master file, created by
   sphinx-quickstart on Sun Feb  9 12:36:23 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flask-SocketIO's documentation!
==========================================

**Flask-SocketIO** gives Flask applications access to low latency bi-direccional communications between the clients and the server. The client-side application can use the `SocketIO <http://socket.io>`_ Javascript library or any compatible client to establish a permanent connection to the server.

Requirements
------------

Flask-SocketIO is based on `gevent-socketio <https://gevent-socketio.readthedocs.org/en/latest/>`_ which in turn depends on `gevent <http://www.gevent.org/>`_ and `gevent-websocket <https://bitbucket.org/Jeffrey/gevent-websocket>`_.

Unfortunately at this time gevent and gevent-socketio only support Python 2.x. There has been some activity in the gevent project towards Python 3 compliance, so support is likely to come in the near future.

Initialization
--------------

The following code example shows how to add Flask-SocketIO to a Flask application::

    from flask import Flask, render_template
    from flask.ext.socketio import SocketIO
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)
    
    if __name__ == '__main__':
        socketio.run(app)

The ``init_app()`` style of initialization is also supported. Note the way the web server is started. The ``socketio.run()`` function encapsulates the start up of the gevent web server. When using this extension the Werkzeug server cannot be used.

Receiving Messages
------------------

When using SocketIO messages are received by both parties as events. On the client side Javascript callbacks are used. With Flask-SocketIO the server needs to register handlers for these events, similarly to how routes are handled by view functions.

The following example creates an event handler for an unnamed event::

    @socketio.on('message')
    def handle_message(message):
        print('received message: ' + message)

The above example uses string messages. Another type of unnamed events use JSON data::

    @socketio.on('json')
    def handle_json(json):
        print('received json: ' + str(json))

The most flexible type of event uses custom names::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))

Named events are the most flexible, as they eliminate the need to include additional metadata to describe the message type.

Flask-SocketIO also supports SocketIO namespaces, which allow the client to multiplex several independent connections on the same physical socket::

    @socketio.on('my event', namespace='/test')
    def handle_my_custom_namespace_event(json):
        print('received json: ' + str(json))

When a namespace is not specified a default global namespace is used.

Sending Messages
----------------

SocketIO event handlers defined as shown in the previous section can send messages to the connected client using the ``send()`` and ``emit()`` functions.

The following examples bounce received events back to the client that sent them::

    from flask.ext.socketio import send, emit

    @socketio.on('message')
    def handle_message(message):
        send(message)

    @socketio.on('json')
    def handle_json(json):
        send(message, json=True)

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json)

Note how ``send()`` and ``emit()`` are used for unnamed and named events respectively.

When working with namespaces ``send()`` and ``emit()`` use the namespace of the incoming message by default. A different namespace can be specified with the optional ``namespace`` argument::

    @socketio.on('message')
    def handle_message(message):
        send(message, namespace='/chat')

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json, namespace='/chat')

SocketIO supports acknowledgement callbacks that confirm that a message was received by the client::

    def ack():
        print 'message was received!'

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json, callback=ack)

When using callbacks the Javascript client receives a callback function to invoke upon receipt of the message. When client calls the callback function the server is notified and invokes the corresponding server-side callback. The client-side can pass arguments in the callback function, which are transferred to the server and given to the server-side callback..

Another very useful feature of SocketIO is the broadcasting of messages. Flask-SocketIO supports this feature with the ``broadcast=True`` optional argument to ``send()`` and ``emit()``::

    @socketio.on('my event')
    def handle_my_custom_event(data):
        emit('my response', data, broadcast=True)

When a message is sent with the broadcast option enabled all clients connected to the namespace receive it, including the sender. When namespaces are not used the clients connected to the global namespace receive the message.

Connection Events
-----------------

Flask-SocketIO also dispatches connection and disconnection events. The following example shows how to register handlers for them::

    @socketio.on('connect', namespace='/chat')
    def test_connect():
        emit('my response', {'data': 'Connected'})

    @socketio.on('disconnect', namespace='/chat')
    def test_disconnect():
        print('Client disconnected')

Note that these events are sent individually on each namespace used. When the global namespace is used only disconnection events are sent due to a limitation in gevent-socketio.

Access to Flask's Context Globals
---------------------------------

Handlers for SocketIO events are different than handlers for routes and that introduces a lot of confusion around what can and cannot be done in a SocketIO handler. The main difference between the two types of handlers is that all the SocketIO events for a client occur in the context of a single long running request.

Flask-SocketIO attempts to make working with SocketIO event handlers easier by making the environment similar to that of a regular HTTP request. The following list describes what works and what doesn't:

- An application context is pushed before invoking an event handler making ``current_app`` and ``g`` available to the handler.
- A fake request context is also pushed before invoking a handler, also making ``request`` and ``session`` available.
- The ``request`` context global is enhanced with a ``namespace`` member. This is the gevent-socketio namespace object, which offers direct access to the socket.
- The ``session`` context global behaves in a different way than in regular requests. The contents of the user session at the time a SocketIO connection is established are made available to the handlers invoked in the context of that connection. Any changes made to the session inside a SocketIO handler are preserved, but only in the SocketIO context, these changes will not be seen by regular HTTP handlers. The technical reason for this limitation is that to save the user session a new cookie needs to be sent to the client, and that requires new HTTP request and response, which do not exist in a socket connection. Handlers can implement their own custom session saving logic if desired.
- In the current release before and after request hooks are not invoked for SocketIO connections. This may be improved in a future release.
