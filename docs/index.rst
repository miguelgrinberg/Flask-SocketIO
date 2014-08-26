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

Current Limitations
~~~~~~~~~~~~~~~~~~~

- Projects gevent and gevent-socketio only support Python 2.x at this time. There has been some activity in the gevent project towards Python 3 compliance, so support for Python 3 is likely to come in the near future.
- The 1.x releases of the Socket.IO client-side Javascript libraries are not compatible with project gevent-socketio. At this time the Socket.IO client release 0.9.16 has been found to be the most stable.

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

The ``init_app()`` style of initialization is also supported. Note the way the web server is started. The ``socketio.run()`` function encapsulates the start up of the gevent web server and replaces the standard Werkzeug development web server, which cannot be used with this extension. However, the Werkzeug debugger and reloader modules are still used when the application is in debug mode.

The application must serve a page to the client that loads the Socket.IO library and establishes a connection::

    <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/socket.io/0.9.16/socket.io.min.js"></script>
    <script type="text/javascript" charset="utf-8">
        var socket = io.connect('http://' + document.domain + ':' + location.port);
        socket.on('connect', function() {
            socket.emit('my event', {data: 'I\'m connected!'});
        });
    </script>

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

The most flexible type of event uses custom event names::

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

When working with namespaces, ``send()`` and ``emit()`` use the namespace of the incoming message by default. A different namespace can be specified with the optional ``namespace`` argument::

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

When using callbacks the Javascript client receives a callback function to invoke upon receipt of the message. When the client calls the callback function the server invokes the corresponding server-side callback. The client can pass arguments in the callback function, which are transferred to the server and given to the server-side callback.

Broadcasting
------------

Another very useful feature of SocketIO is the broadcasting of messages. Flask-SocketIO supports this feature with the ``broadcast=True`` optional argument to ``send()`` and ``emit()``::

    @socketio.on('my event')
    def handle_my_custom_event(data):
        emit('my response', data, broadcast=True)

When a message is sent with the broadcast option enabled all clients connected to the namespace receive it, including the sender. When namespaces are not used the clients connected to the global namespace receive the message. Note that callbacks are not invoked for broadcast messages.

Sometimes the server needs to be the originator of a message. This can be useful to send a notification to clients of an event that originated in the server. The ``socketio.send()`` and ``socketio.emit()`` methods can be used to broadcast to all connected clients::

    def some_function():
        socketio.emit('some event', {'data': 42})

Note that in this usage the ``broadcast=True`` argument is assumed and does not need to be specified.

Rooms
-----

For many applications it is necessary to group users dynamically and send messages to them. The best example is a chat application with multiple rooms, where users receive messages from the room or rooms they are in, but not from other rooms where other users are. Flask-SocketIO supports this concept of rooms through the ``join_room()`` and ``leave_room()`` functions::

    from flask.ext.socketio import join_room, leave_room

    @socketio.on('join')
    def on_join(data):
        username = data['username']
        room = data['room']
        join_room(room)
        send(username + ' has entered the room.', room=room)

    @socketio.on('leave')
    def on_leave(data):
        username = data['username']
        room = data['room']
        leave_room(room)
        send(username + ' has left the room.', room=room)

The ``send()`` and ``emit()`` functions accept an optional ``room`` argument that cause the message to be sent to all the clients that are in the given room. A given client can join multiple rooms if desired. When a client disconnects it is removed from any room it was in.

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
- A request context is also pushed before invoking a handler, also making ``request`` and ``session`` available. Note that WebSocket events do not have individual requests associated with them, so the request context will be based on the request that started the WebSocket connection.
- The ``request`` context global is enhanced with a ``namespace`` member. This is the gevent-socketio namespace object, which offers direct access to the low level socket.
- The ``session`` context global behaves in a different way than in regular requests. A copy of the user session at the time the SocketIO connection is established is made available to handlers invoked in the context of that connection. Any changes made to the session inside a SocketIO handler are preserved, but only in the SocketIO context, these changes will not be seen by regular HTTP handlers. The technical reason for this limitation is that to save the user session a cookie needs to be sent to the client, and that requires HTTP request and response, which do not exist in a socket connection. When using server-side session storage SocketIO handlers can update user sessions even for HTTP routes (see the `Flask-KVsession <https://github.com/mbr/flask-kvsession/>`_ extension).
- Before and after request hooks are not invoked for SocketIO connections.

Deployment
----------

The simplest deployment strategy is to start the web server by calling ``socketio.run(app)`` as shown above, but with debug mode turned off in the configuration. This will run the application on the gevent-socketio web server, which is based on gevent.

An alternative is to use `gunicorn <http://gunicorn.org/>`_ as web server, using the worker class provided by gevent-socketio. The command line that starts the server in this way is shown below::

    gunicorn --worker-class socketio.sgunicorn.GeventSocketIOWorker module:app

In this command ``module`` is the Python module or package that defines the application instance, and ``app`` is the application instance itself.

Note regarding `uWSGI <http://uwsgi-docs.readthedocs.org/en/latest/>`_: While this server has support for gevent and WebSocket, there is no way to use the custom event loop needed by gevent-socketio, so there is no directly available method for hosting Flask-SocketIO applications on it. If you figure out how to do this please let me know!

Using nginx as a WebSocket Reverse Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to use nginx as a front-end reverse proxy that passes requests to the application. However, it is important to note that only releases of nginx 1.4 and newer support proxying of the WebSocket protocol. Below is an example nginx configuration that proxies regular and WebSocket requests::

    server {
        listen 80;
        server_name localhost;
        access_log /var/log/nginx/example.log;

        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_redirect off;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /socket.io {
            proxy_pass http://127.0.0.1:5000/socket.io;
            proxy_redirect off;
            proxy_buffering off;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
        }
    }
