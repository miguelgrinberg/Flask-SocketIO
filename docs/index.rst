.. Flask-SocketIO documentation master file, created by
   sphinx-quickstart on Sun Feb  9 12:36:23 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flask-SocketIO's documentation!
==========================================

**Flask-SocketIO** gives Flask applications access to low latency
bi-directional communications between the clients and the server. The
client-side application can use any of the `SocketIO <http://socket.io>`_
official clients libraries in Javascript, C++, Java and Swift, or any
compatible client to establish a permanent connection to the server.

Installation
------------

You can install this package in the usual way using ``pip``::

    pip install flask-socketio

Requirements
------------

Flask-SocketIO is compatible with Python 3.6+. The asynchronous services that
this package relies on can be selected among three choices:

- `eventlet <http://eventlet.net/>`_ is the best performant option, with
  support for long-polling and WebSocket transports.
- `gevent <http://www.gevent.org/>`_ is supported in a number of different
  configurations. The long-polling transport is fully supported with the
  gevent package, but unlike eventlet, gevent does not have native WebSocket
  support. To add support for WebSocket there are currently two options.
  Installing the `gevent-websocket <https://pypi.python.org/pypi/gevent-websocket/>`_
  package adds WebSocket support to gevent or one can use the `uWSGI
  <https://uwsgi-docs.readthedocs.io/en/latest/>`_ web server, which
  comes with WebSocket functionality. The use of gevent is also a performant
  option, but slightly lower than eventlet.
- The Flask development server based on Werkzeug can be used as well, with the
  caveat that it lacks the performance of the other two options, so it should
  only be used to simplify the development workflow. This option only supports
  the long-polling transport.

The extension automatically detects which asynchronous framework to use based
on what is installed. Preference is given to eventlet, followed by gevent.
For WebSocket support in gevent, uWSGI is preferred, followed by
gevent-websocket. If neither eventlet nor gevent are installed, then the Flask
development server is used.

If using multiple processes, a message queue service is used by the processes
to coordinate operations such as broadcasting. The supported queues are
`Redis <http://redis.io/>`_, `RabbitMQ <https://www.rabbitmq.com/>`_,
`Kafka <http://kafka/apache.org/>`_, and any
other message queues supported by the
`Kombu <http://kombu.readthedocs.org/en/latest/>`_ package.

On the client-side, the official Socket.IO Javascript client library can be
used to establish a connection to the server. There are also official clients
written in Swift, Java and C++. Unofficial clients may also work, as long as
they implement the
`Socket.IO protocol <https://github.com/socketio/socket.io-protocol>`_.
The `python-socketio <https://github.com/miguelgrinberg/python-socketio>`_
package includes a Python client.

Version compatibility
---------------------

The Socket.IO protocol has been through a number of revisions, and some of these
introduced backward incompatible changes, which means that the client and the
server must use compatible versions for everything to work.

The version compatibility chart below maps versions of this package to versions
of the JavaScript reference implementation and the versions of the Socket.IO and
Engine.IO protocols.

+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+
| JavaScript Socket.IO version | Socket.IO protocol revision | Engine.IO protocol revision | Flask-SocketIO version | python-socketio version |
+==============================+=============================+=============================+========================+=========================+
| 0.9.x                        | 1, 2                        | 1, 2                        | Not supported          | Not supported           |
+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+
| 1.x and 2.x                  | 3, 4                        | 3                           | 4.x                    | 4.x                     |
+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+
| 3.x                          | 5                           | 4                           | 5.x                    | 5.x                     |
+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+

Initialization
--------------

The following code example shows how to add Flask-SocketIO to a Flask
application::

    from flask import Flask, render_template
    from flask_socketio import SocketIO

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)

    if __name__ == '__main__':
        socketio.run(app)

The ``init_app()`` style of initialization is also supported. To start the
web server simply execute your script. Note the way the web server is started.
The ``socketio.run()`` function encapsulates the start up of the web server and
replaces the ``app.run()`` standard Flask development server start up. When the
application is in debug mode the Werkzeug development server is still used and
configured properly inside ``socketio.run()``. In production mode the eventlet
web server is used if available, else the gevent web server is used. If
eventlet and gevent are not installed, the Werkzeug development web server is
used.

The ``flask run`` command introduced in Flask 0.11 can be used to start a
Flask-SocketIO development server based on Werkzeug, but this method of starting
the Flask-SocketIO server is not recommended due to lack of WebSocket support.
Previous versions of this package included a customized version of the
``flask run`` command that allowed the use of WebSocket on eventlet and gevent
production servers, but this functionality has been discontinued in favor of the
``socketio.run(app)`` startup method shown above which is more robust.

The application must serve a page to the client that loads the Socket.IO
library and establishes a connection::

    <script src="//cdnjs.cloudflare.com/ajax/libs/socket.io/2.2.0/socket.io.js" integrity="sha256-yr4fRk/GU1ehYJPAs8P4JlTgu0Hdsp4ZKrx8bDEDC3I=" crossorigin="anonymous"></script>
    <script type="text/javascript" charset="utf-8">
        var socket = io();
        socket.on('connect', function() {
            socket.emit('my event', {data: 'I\'m connected!'});
        });
    </script>

Receiving Messages
------------------

When using SocketIO, messages are received by both parties as events. On the
client side Javascript callbacks are used. With Flask-SocketIO the server
needs to register handlers for these events, similarly to how routes are
handled by view functions.

The following example creates a server-side event handler for an unnamed
event::

    @socketio.on('message')
    def handle_message(data):
        print('received message: ' + data)

The above example uses string messages. Another type of unnamed events use
JSON data::

    @socketio.on('json')
    def handle_json(json):
        print('received json: ' + str(json))

The most flexible type of event uses custom event names. The message data for
these events can be string, bytes, int, or JSON::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))

Custom named events can also support multiple arguments::

    @socketio.on('my_event')
    def handle_my_custom_event(arg1, arg2, arg3):
        print('received args: ' + arg1 + arg2 + arg3)

When the name of the event is a valid Python identifier that does not collide
with other defined symbols, the ``@socketio.event`` provides a more compact
syntax that takes the event name from the decorated function::

    @socketio.event
    def my_custom_event(arg1, arg2, arg3):
        print('received args: ' + arg1 + arg2 + arg3)

Named events are the most flexible, as they eliminate the need to include
additional metadata to describe the message type. The names ``message``,
``json``, ``connect`` and ``disconnect`` are reserved and cannot be used for
named events.

Flask-SocketIO also supports SocketIO namespaces, which allow the client to
multiplex several independent connections on the same physical socket::

    @socketio.on('my event', namespace='/test')
    def handle_my_custom_namespace_event(json):
        print('received json: ' + str(json))

When a namespace is not specified a default global namespace with the name
``'/'`` is used.

For cases when a decorator syntax isn't convenient, the ``on_event`` method
can be used::

    def my_function_handler(data):
        pass

    socketio.on_event('my event', my_function_handler, namespace='/test')

Clients may request an acknowledgement callback that confirms receipt of a
message they sent. Any values returned from the handler function will be
passed to the client as arguments in the callback function::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))
        return 'one', 2

In the above example, the client callback function will be invoked with
two arguments, ``'one'`` and ``2``. If a handler function does not return any
values, the client callback function will be invoked without arguments.

Sending Messages
----------------

SocketIO event handlers defined as shown in the previous section can send
reply messages to the connected client using the ``send()`` and ``emit()``
functions.

The following examples bounce received events back to the client that sent
them::

    from flask_socketio import send, emit

    @socketio.on('message')
    def handle_message(message):
        send(message)

    @socketio.on('json')
    def handle_json(json):
        send(json, json=True)

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json)

Note how ``send()`` and ``emit()`` are used for unnamed and named events
respectively.

When working with namespaces, ``send()`` and ``emit()`` use the namespace of
the incoming message by default. A different namespace can be specified with
the optional ``namespace`` argument::

    @socketio.on('message')
    def handle_message(message):
        send(message, namespace='/chat')

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json, namespace='/chat')

To send an event with multiple arguments, send a tuple::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', ('foo', 'bar', json), namespace='/chat')

SocketIO supports acknowledgment callbacks that confirm that a message was
received by the client::

    def ack():
        print 'message was received!'

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json, callback=ack)

When using callbacks, the Javascript client receives a callback function to
invoke upon receipt of the message. After the client application invokes the
callback function the server invokes the corresponding server-side callback.
If the client-side callback is invoked with arguments, these are provided as
arguments to the server-side callback as well.

Broadcasting
------------

Another very useful feature of SocketIO is the broadcasting of messages.
Flask-SocketIO supports this feature with the ``broadcast=True`` optional
argument to ``send()`` and ``emit()``::

    @socketio.on('my event')
    def handle_my_custom_event(data):
        emit('my response', data, broadcast=True)

When a message is sent with the broadcast option enabled, all clients
connected to the namespace receive it, including the sender. When namespaces
are not used, the clients connected to the global namespace receive the
message. Note that callbacks are not invoked for broadcast messages.

In all the examples shown until this point the server responds to an event
sent by the client. But for some applications, the server needs to be the
originator of a message. This can be useful to send notifications to clients
of events that originated in the server, for example in a background thread.
The ``socketio.send()`` and ``socketio.emit()`` methods can be used to
broadcast to all connected clients::

    def some_function():
        socketio.emit('some event', {'data': 42})

Note that ``socketio.send()`` and ``socketio.emit()`` are not the same
functions as the context-aware ``send()`` and ``emit()``. Also note that in the
above usage there is no client context, so ``broadcast=True`` is assumed and
does not need to be specified.

Rooms
-----

For many applications it is necessary to group users into subsets that can be
addressed together. The best example is a chat application with multiple rooms,
where users receive messages from the room or rooms they are in, but not from
other rooms where other users are. Flask-SocketIO supports this concept of
rooms through the ``join_room()`` and ``leave_room()`` functions::

    from flask_socketio import join_room, leave_room

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

The ``send()`` and ``emit()`` functions accept an optional ``room`` argument
that cause the message to be sent to all the clients that are in the given
room.

All clients are assigned a room when they connect, named with the session ID
of the connection, which can be obtained from ``request.sid``. A given client
can join any rooms, which can be given any names. When a client disconnects it
is removed from all the rooms it was in. The context-free ``socketio.send()``
and ``socketio.emit()`` functions also accept a ``room`` argument to broadcast
to all clients in a room.

Since all clients are assigned a personal room, to address a message to a
single client, the session ID of the client can be used as the room argument.

Connection Events
-----------------

Flask-SocketIO also dispatches connection and disconnection events. The
following example shows how to register handlers for them::

    @socketio.on('connect')
    def test_connect():
        emit('my response', {'data': 'Connected'})

    @socketio.on('disconnect')
    def test_disconnect():
        print('Client disconnected')

The connection event handler can return ``False`` to reject the connection, or
it can also raise `ConectionRefusedError`. This is so that the client can be
authenticated at this point. When using the exception, any arguments passed to
the exception are returned to the client in the error packet. Examples::

    from flask_socketio import ConnectionRefusedError

    @socketio.on('connect')
    def connect():
        if not self.authenticate(request.args):
            raise ConnectionRefusedError('unauthorized!')

Note that connection and disconnection events are sent individually on each
namespace used.

Class-Based Namespaces
----------------------

As an alternative to the decorator-based event handlers described above, the
event handlers that belong to a namespace can be created as methods of a
class. The :class:`flask_socketio.Namespace` is provided as a base class to
create class-based namespaces::

    from flask_socketio import Namespace, emit

    class MyCustomNamespace(Namespace):
        def on_connect(self):
            pass

        def on_disconnect(self):
            pass

        def on_my_event(self, data):
            emit('my_response', data)

    socketio.on_namespace(MyCustomNamespace('/test'))

When class-based namespaces are used, any events received by the server are
dispatched to a method named as the event name with the ``on_`` prefix. For
example, event ``my_event`` will be handled by a method named ``on_my_event``.
If an event is received for which there is no corresponding method defined in
the namespace class, then the event is ignored. All event names used in
class-based namespaces must use characters that are legal in method names.

As a convenience to methods defined in a class-based namespace, the namespace
instance includes versions of several of the methods in the
:class:`flask_socketio.SocketIO` class that default to the proper namespace
when the ``namespace`` argument is not given.

If an event has a handler in a class-based namespace, and also a
decorator-based function handler, only the decorated function handler is
invoked.

Error Handling
--------------

Flask-SocketIO can also deal with exceptions::

    @socketio.on_error()        # Handles the default namespace
    def error_handler(e):
        pass

    @socketio.on_error('/chat') # handles the '/chat' namespace
    def error_handler_chat(e):
        pass

    @socketio.on_error_default  # handles all namespaces without an explicit error handler
    def default_error_handler(e):
        pass

Error handler functions take the exception object as an argument.

The message and data arguments of the current request can also be inspected
with the ``request.event`` variable, which is useful for error logging and
debugging outside the event handler::

    from flask import request

    @socketio.on("my error event")
    def on_my_event(data):
        raise RuntimeError()

    @socketio.on_error_default
    def default_error_handler(e):
        print(request.event["message"]) # "my error event"
        print(request.event["args"])    # (data,)

Debugging and Troubleshooting
-----------------------------

To help you debug issues, the server can be configured to output logs to the
terminal::

    socketio = SocketIO(logger=True, engineio_logger=True)

The ``logger`` argument controls logging related to the Socket.IO protocol,
while ``engineio_logger`` controls logs that originate in the low-level
Engine.IO transport. These arguments can be set to ``True`` to output logs to
``stderr``, or to an object compatible with Python's ``logging`` package
where the logs should be emitted to. A value of ``False`` disables logging.

Logging can help identify the cause of connection problems, 400 responses,
bad performance and other issues.

Access to Flask's Context Globals
---------------------------------

Handlers for SocketIO events are different than handlers for routes and that
introduces a lot of confusion around what can and cannot be done in a SocketIO
handler. The main difference is that all the SocketIO events generated for a
client occur in the context of a single long running request.

In spite of the differences, Flask-SocketIO attempts to make working with
SocketIO event handlers easier by making the environment similar to that of a
regular HTTP request. The following list describes what works and what doesn't:

- An application context is pushed before invoking an event handler making
  ``current_app`` and ``g`` available to the handler.
- A request context is also pushed before invoking a handler, also making
  ``request`` and ``session`` available. But note that WebSocket events do not
  have individual requests associated with them, so the request context that
  started the connection is pushed for all the events that are dispatched
  during the life of the connection.
- The ``request`` context global is enhanced with a ``sid`` member that is set
  to a unique session ID for the connection. This value is used as an initial
  room where the client is added.
- The ``request`` context global is enhanced with ``namespace`` and ``event``
  members that contain the currently handled namespace and event arguments.
  The ``event`` member is a dictionary with ``message`` and ``args`` keys.
- The ``session`` context global behaves in a different way than in regular
  requests. A copy of the user session at the time the SocketIO connection is
  established is made available to handlers invoked in the context of that
  connection. If a SocketIO handler modifies the session, the modified session
  will be preserved for future SocketIO handlers, but regular HTTP route
  handlers will not see these changes. Effectively, when a SocketIO handler
  modifies the session, a "fork" of the session is created exclusively for
  these handlers. The technical reason for this limitation is that to save the
  user session a cookie needs to be sent to the client, and that requires HTTP
  request and response, which do not exist in a SocketIO connection. When
  using server-side sessions such as those provided by the Flask-Session or
  Flask-KVSession extensions, changes made to the session in HTTP route
  handlers can be seen by SocketIO handlers, as long as the session is not
  modified in the SocketIO handlers.
- The ``before_request`` and ``after_request`` hooks are not invoked for
  SocketIO event handlers.
- SocketIO handlers can take custom decorators, but most Flask decorators will
  not be appropriate to use for a SocketIO handler, given that there is no
  concept of a ``Response`` object during a SocketIO connection.

Authentication
--------------

A common need of applications is to validate the identity of their users. The
traditional mechanisms based on web forms and HTTP requests cannot be used in
a SocketIO connection, since there is no place to send HTTP requests and
responses. If necessary, an application can implement a customized login form
that sends credentials to the server as a SocketIO message when the submit
button is pressed by the user.

However, in most cases it is more convenient to perform the traditional
authentication process before the SocketIO connection is established. The
user's identity can then be recorded in the user session or in a cookie, and
later when the SocketIO connection is established that information will be
accessible to SocketIO event handlers.

Using Flask-Login with Flask-SocketIO
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flask-SocketIO can access login information maintained by
`Flask-Login <https://flask-login.readthedocs.org/en/latest/>`_. After a
regular Flask-Login authentication is performed and the ``login_user()``
function is called to record the user in the user session, any SocketIO
connections will have access to the ``current_user`` context variable::

    @socketio.on('connect')
    def connect_handler():
        if current_user.is_authenticated:
            emit('my response',
                 {'message': '{0} has joined'.format(current_user.name)},
                 broadcast=True)
        else:
            return False  # not allowed here

Note that the ``login_required`` decorator cannot be used with SocketIO event
handlers, but a custom decorator that disconnects non-authenticated users can
be created as follows::

    import functools
    from flask import request
    from flask_login import current_user
    from flask_socketio import disconnect, emit

    def authenticated_only(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                disconnect()
            else:
                return f(*args, **kwargs)
        return wrapped

    @socketio.on('my event')
    @authenticated_only
    def handle_my_custom_event(data):
        emit('my response', {'message': '{0} has joined'.format(current_user.name)},
             broadcast=True)

Deployment
----------

There are many options to deploy a Flask-SocketIO server, ranging from simple
to the insanely complex. In this section, the most commonly used options are
described.

Embedded Server
~~~~~~~~~~~~~~~

The simplest deployment strategy is to have eventlet or gevent installed, and
start the web server by calling ``socketio.run(app)`` as shown in examples
above. This will run the application on the eventlet or gevent web servers,
whichever is installed.

Note that ``socketio.run(app)`` runs a production ready server when eventlet
or gevent are installed. If neither of these are installed, then the
application runs on Flask's development web server, which is not appropriate
for production use.

Unfortunately this option is not available when using gevent with uWSGI. See
the uWSGI section below for information on this option.

Gunicorn Web Server
~~~~~~~~~~~~~~~~~~~

An alternative to ``socketio.run(app)`` is to use
`gunicorn <http://gunicorn.org/>`_ as web server, using the eventlet or gevent
workers. For this option, eventlet or gevent need to be installed, in addition
to gunicorn. The command line that starts the eventlet server via gunicorn is::

    gunicorn --worker-class eventlet -w 1 module:app

If you prefer to use gevent, the command to start the server is::

    gunicorn -k gevent -w 1 module:app

When using gunicorn with the gevent worker and the WebSocket support provided
by gevent-websocket, the command that starts the server must be changed to
select a custom gevent web server that supports the WebSocket protocol. The
modified command is::

    gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 module:app

In all these commands, ``module`` is the Python module or package that defines
the application instance, and ``app`` is the application instance itself.

Due to the limited load balancing algorithm used by gunicorn, it is not possible
to use more than one worker process when using this web server. For that reason,
all the examples above include the ``-w 1`` option.

uWSGI Web Server
~~~~~~~~~~~~~~~~

When using the uWSGI server in combination with gevent, the Socket.IO server
can take advantage of uWSGI’s native WebSocket support.

A complete explanation of the configuration and usage of the uWSGI server is
beyond the scope of this documentation. The uWSGI server is a fairly complex
package that provides a large and comprehensive set of options. It must be
compiled with WebSocket and SSL support for the WebSocket transport to be
available. As way of an introduction, the following command starts a uWSGI
server for the example application app.py on port 5000::

    $ uwsgi --http :5000 --gevent 1000 --http-websockets --master --wsgi-file app.py --callable app

Using nginx as a WebSocket Reverse Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to use nginx as a front-end reverse proxy that passes requests
to the application. However, only releases of nginx 1.4 and newer support
proxying of the WebSocket protocol. Below is a basic nginx configuration that
proxies HTTP and WebSocket requests::

    server {
        listen 80;
        server_name _;

        location / {
            include proxy_params;
            proxy_pass http://127.0.0.1:5000;
        }

        location /static {
            alias <path-to-your-application>/static;
            expires 30d;
        }

        location /socket.io {
            include proxy_params;
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_pass http://127.0.0.1:5000/socket.io;
        }
    }

The next example adds the support for load balancing multiple Socket.IO
servers::

    upstream socketio_nodes {
        ip_hash;

        server 127.0.0.1:5000;
        server 127.0.0.1:5001;
        server 127.0.0.1:5002;
        # to scale the app, just add more nodes here!
    }

    server {
        listen 80;
        server_name _;

        location / {
            include proxy_params;
            proxy_pass http://127.0.0.1:5000;
        }

        locaton /static {
            alias <path-to-your-application>/static;
            expires 30d;
        }

        location /socket.io {
            include proxy_params;
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_pass http://socketio_nodes/socket.io;
        }
    }

While the above examples can work as an initial configuration, be aware that a
production install of nginx will need a more complete configuration covering
other deployment aspects such as serving static file assets and SSL support.

Using Multiple Workers
~~~~~~~~~~~~~~~~~~~~~~

Flask-SocketIO supports multiple workers behind a load balancer starting with
release 2.0. Deploying multiple workers gives applications that use
Flask-SocketIO the ability to spread the client connections among multiple
processes and hosts, and in this way scale to support very large numbers of
concurrent clients.

There are two requirements to use multiple Flask-SocketIO workers:

- The load balancer must be configured to forward all HTTP requests from a
  given client always to the same worker. This is sometimes referenced as
  "sticky sessions". For nginx, use the ``ip_hash`` directive to achieve this.
  Gunicorn cannot be used with multiple workers because its load balancer
  algorithm does not support sticky sessions.

- Since each of the servers owns only a subset of the client connections, a
  message queue such as Redis or RabbitMQ is used by the servers to coordinate
  complex operations such as broadcasting and rooms.

When working with a message queue, there are additional dependencies that need to
be installed:

- For Redis, the package ``redis`` must be installed (``pip install redis``).
- For RabbitMQ, the package ``kombu`` must be installed (``pip install kombu``).
- For Kafka, the package ``kafka-python`` must be installed (``pip install kafka-python``).
- For other message queues supported by Kombu, see the `Kombu documentation
  <http://docs.celeryproject.org/projects/kombu/en/latest/introduction.html#transport-comparison>`_
  to find out what dependencies are needed.
- If eventlet or gevent are used, then monkey patching the Python standard
  library is normally required to force the message queue package to use
  coroutine friendly functions and classes.

For eventlet, monkey patching is done with::

   import eventlet
   eventlet.monkey_patch()

For gevent, you can monkey patch the standard library with::

    from gevent import monkey
    monkey.patch_all()

In both cases it is recommended that you apply the monkey patching at the top
of your main script, even above your imports.

To start multiple Flask-SocketIO servers, you must first ensure you have the
message queue service running. To start a Socket.IO server and have it connect to
the message queue, add the ``message_queue`` argument to the ``SocketIO``
constructor::

    socketio = SocketIO(app, message_queue='redis://')

The value of the ``message_queue`` argument is the connection URL of the
queue service that is used. For a redis queue running on the same host as the
server, the ``'redis://'`` URL can be used. Likewise, for a default RabbitMQ
queue the ``'amqp://'`` URL can be used. For Kafka, use a ``kafka://`` URL.
The Kombu package has a `documentation
section <http://docs.celeryproject.org/projects/kombu/en/latest/userguide/connections.html?highlight=urls#urls>`_
that describes the format of the URLs for all the supported queues.

Emitting from an External Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For many types of applications, it is necessary to emit events from a process
that is not the SocketIO server, for an example a Celery worker. If the
SocketIO server or servers are configured to listen on a message queue as
shown in the previous section, then any other process can create its own
``SocketIO`` instance and use it to emit events in the same way the server
does.

For example, for an application that runs on an eventlet web server and uses
a Redis message queue, the following Python script broadcasts an event to
all clients::

    socketio = SocketIO(message_queue='redis://')
    socketio.emit('my event', {'data': 'foo'}, namespace='/test')

When using the ``SocketIO`` instance in this way, the Flask application
instance is not passed to the constructor.

The ``channel`` argument to ``SocketIO`` can be used to select a specific
channel of communication through the message queue. Using a custom channel
name is necessary when there are multiple independent SocketIO services
sharing the same queue.

Flask-SocketIO does not apply monkey patching when eventlet or gevent are
used. But when working with a message queue, it is very likely that the Python
package that talks to the message queue service will hang if the Python
standard library is not monkey patched.

It is important to note that an external process that wants to connect to
a SocketIO server does not need to use eventlet or gevent like the main
server. Having a server use a coroutine framework, while an external process
is not a problem. For example, Celery workers do not need to be
configured to use eventlet or gevent just because the main server does. But if
your external process does use a coroutine framework for whatever reason, then
monkey patching is likely required, so that the message queue accesses
coroutine friendly functions and classes.

Cross-Origin Controls
---------------------

For security reasons, this server enforces a same-origin policy by default. In
practical terms, this means the following:

- If an incoming HTTP or WebSocket request includes the ``Origin`` header,
  this header must match the scheme and host of the connection URL. In case
  of a mismatch, a 400 status code response is returned and the connection is
  rejected.
- No restrictions are imposed on incoming requests that do not include the
  ``Origin`` header.

If necessary, the ``cors_allowed_origins`` option can be used to allow other
origins. This argument can be set to a string to set a single allowed origin, or
to a list to allow multiple origins. A special value of ``'*'`` can be used to
instruct the server to allow all origins, but this should be done with care, as
this could make the server vulnerable to Cross-Site Request Forgery (CSRF)
attacks.

Upgrading to Flask-SocketIO 5.x from the 4.x releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Socket.IO protocol recently introduced a series of backwards incompatible
changes. The 5.x releases of Flask-SocketIO adopted these changes, and for
that reason it can only be used with clients that have also been updated to
the current version of the protocol. In particular, this means that the
JavaScript client must be upgraded to a 3.x release, and if your client hasn't
been upgraded to the latest version of the Socket.IO protocol, then you must
use a Flask-SocketIO 4.x release.

The following protocol changes are of importance, as they may affect existing
applications:

- The default namespace ``'/'`` is not automatically connected anymore, and is
  now treated in the same way as other namespaces.
- Each namespace connection has its own ``sid`` value, different from the others
  and different from the Engine.IO ``sid``.
- Flask-SocketIO now uses the same ping interval and timeout values as the
  JavaScript reference implementation, which are 25 and 5 seconds respectively.
- The ping/pong mechanism has been reversed. In the current version of the
  protocol, the server issues a ping and the client responds with a pong.
- The default allowed payload size for long--polling packets has been lowered
  from 100MB to 1MB.
- The `io` cookie is not sent to the client anymore by default.

API Reference
-------------

.. module:: flask_socketio
.. autoclass:: SocketIO
   :members:
.. autofunction:: emit
.. autofunction:: send
.. autofunction:: join_room
.. autofunction:: leave_room
.. autofunction:: close_room
.. autofunction:: rooms
.. autofunction:: disconnect
.. autoclass:: Namespace
   :members:
.. autoclass:: SocketIOTestClient
   :members:
