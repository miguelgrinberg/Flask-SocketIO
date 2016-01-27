.. Flask-SocketIO documentation master file, created by
   sphinx-quickstart on Sun Feb  9 12:36:23 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

欢迎来到 Flask-SocketIO 中文文档!
===============================

**Flask-SocketIO** 使得 Flask 应用在服务端和客户端的双向通信中延迟更低。
客户端的应用程序可以使用任何Javascript，  C++, Java 和 Swift 的官方的客户端库，
或者其他任何官方的`SocketIO <http://socket.io>`_ 客户端，
与服务端简历永久的链接。

安装
-------------------------------

你可以使用 ``pip`` 安装这个包：

    pip install flask-socketio

依赖
------------

自从 1.0 版本以来，这个扩展便支持 Python2.7 和 Python 3.3+ 了。
这个包所依赖的异步服务器可以从下面三个中任选其一即可:

- `eventlet <http://eventlet.net/>`_ 从性能上来说是目前最好的选择，
  它支持长 long-polling 和 WebSocket transports。

- `gevent <http://www.gevent.org/>`_ 是这个扩展早期版本使用的框架。
  long-polling 是完全支持的，但是如果要想支持 WebSocket，就必须将
  `gevent-websocket <https://pypi.python.org/pypi/gevent-websocket/>`_ 安装好。
  使用 gevent 和 gevent-websocket 性能也很不错，不过要比 eventlet 稍微低一点点。

- 基于 Werkzeug 的 Flask 开发服务器也可以被很好的使用，但是需要提醒的是，它的性能远不如
  其他两个可选方案，因此它应该仅用作来简化开发流程。这个选项仅支持long-polling transport。

这个扩展将根据你所安装的异步框架来自动选择，优先选择 eventlet，其次是 gevent。
如果这两个都没有被安装，将会使用 Flask 开发服务器。

如果使用多个进程，将使用一个消息队列来协调操作。
支持队列的有 `Redis <http://redis.io/>`_, `RabbitMQ <https://www.rabbitmq.com/>`_,
The supported queues are
`Redis <http://redis.io/>`_, `RabbitMQ <https://www.rabbitmq.com/>`_, 或者其他任何支持
`Kombu <http://kombu.readthedocs.org/en/latest/>`_ 包的消息队列。

在客户端，官方的 Socket.IO Javascript 客户端库可以用于建立与服务器的链接。
也有用 Swift， Java， C++ 写的官方客户端。非官方的客户端，只要实现了
`Socket.IO protocol <https://github.com/socketio/socket.io-protocol>`_. 也行。


与 Flask-SocketIO 0.x 版本的差异
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

旧版本的 Flask-SocketIO 有着完全不同的依赖关系。
这些老版本依赖的
`gevent-socketio <https://gevent-socketio.readthedocs.org/en/latest/>`_ 和
`gevent-websocket <https://pypi.python.org/pypi/gevent-websocket/>`_, 在 1.0 版本都不再依赖.

尽管依赖关系有变化，但是在1.0 版本中并没有什么显著的变化。
下面是实际的差异列表：

- 1.0 版本删除了对 Python 2.6 的支持， 并且添加了对 Python 3.3, Python 3.4 和 pypy 的支持.
- 使用 0.x 版本需要一个老版本的 Socket.IO Javascript 客户端.
  从 1.0 版本开始，可支持 Socket.IO 和 Engine.IO 当前的版本.
  Releases of the Socket.IO client prior to 1.0 are no supported.
  Swift 和 C++ 官方的 Socket.IO 客户端也可以很好的支持.
- 0.x 版本 依赖与 gevent，gevent-socketio 和 gevent-websocket.
  在 1.0 版本中， 将不再使用 gevent-socketio ,
  并且 gevent 是三个后端 web server 选项中一个, 包括 eventlet 和 任何常规的多线程 WSGI 服务器，以及 Flask 的 开发服务器.
- Socket.IO 服务器选项已经在 1.0 版本更改.
  他们可以在 SocketIO 的构造函数中被提供，或者通过 ``run()`` 调用.
  这提供的两个选项在使用前已经被合并。
- 0.x 版本使用 ``request.namespace`` 暴露了 gevent-socketio 的连接.
  在 1.0 版本这些将不再可用.
  请求对象 ``request.namespace`` 作为命名空间被处理，并且添加了 ``request.sid``，
  定义为客户端链接会话的唯一id，并且 ``request.event`` 中包含了事情名称和参数.
- To get the list of rooms a client was in the 0.x release required the
  application to use a private structure of gevent-socketio, with the
  expression ``request.namespace.rooms``. This is not available in release
  1.0, which includes a proper ``rooms()`` function.
- 推荐的 "trick" 是发送一条消息给一个客户端，是将他们单独放到一个房间里，然后发送消息到这个房间.
  这就是 1.0 版本，当客户端连接时将自动分配给他们一个房间.
- The ``'connect'`` event for the global namespace did not fire on releases
  prior to 1.0. This has been fixed and now this event fires as expected.
- Support for client-side callbacks was introduced in release 1.0.

从更早的版本升级 Flask-SocketIO 到 1.x 和 2.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在客户端，你需要去升级你的 Socket.IO Javascript 客户端 到 1.3.x 或者更新.

在客户端，有一些需要考虑的地方：

- 如果你希望继续使用 gevent， 然后你需要从你的虚拟环境中卸载 gevent-socketio ，
  因为不再使用该软件包，并且可能与他的替代软件包 python-socketio 发生冲突.
- 如果你希望有个较好的性能和稳定性，建议你切换到 eventlet. 为了做到这一点，
  卸载 gevent， gevent-socketio 和 gevent-websocket, 然后安装 eventlet.
- 如果你的应用使用 monkey patching 并且你切换到了 eventlet, 调用 `eventlet.monkey_patch()`
  替代 gevent 的 `monkey.patch_all()` . 此外，任何调用 gevent 都必须替换成相当与调用 eventlet.
- 任何使用 `request.namespace` 都必须替换成直接调用 Flask-SocketIO 的方法.
  例如，`request.namespace.rooms` 必须替换成 `rooms()` 方法.
- 内部的任何 gevent-socketio 对象都必须移除, 因为已经不再依赖与这个包了.

安装
--------------

下面的代码演示了如何添加 Flask-SocketIO 到 一个 Flask 应用中::

    from flask import Flask, render_template
    from flask_socketio import SocketIO

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)

    if __name__ == '__main__':
        socketio.run(app)

同样也支持 ``init_app()`` 的初始化风格. 注意这个 web server 启动的方法.
``socketio.run()`` 封装了 web server 的启动并且替代了 Flask 开发环境标准的启动方式 ``app.run()`` .
当应用在 debug 模式下，Werkzeug 开发服务器依然在使用并且正确配置了 ``socketio.run()`` .
在生产环境中，如果 eventlet 可用的话将使用 eventlet， 否则将会使用 gevent .
如果 eventlet 和 gevent 都没有被安装, 将使用 Werkzeug 的开发服务器.

应用程序必须服务一个客户端页面以此来加载 Socket.IO 库和建立一个连接::

    <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/socket.io/1.3.6/socket.io.min.js"></script>
    <script type="text/javascript" charset="utf-8">
        var socket = io.connect('http://' + document.domain + ':' + location.port);
        socket.on('connect', function() {
            socket.emit('my event', {data: 'I\'m connected!'});
        });
    </script>

接收消息
------------------

当使用 SocketIO, 接收到消息是双方的事件.在客户端 Javascript 回调将被使用.
使用 Flask-SocketIO 服务端需要注册这些事件的处理，类似与路由是如何通过视图函数处理的.

下面的示例为一个没有定义的事件创建了一个服务端事件处理::

    @socketio.on('message')
    def handle_message(message):
        print('received message: ' + message)

上面的例子使用字符串消息. 另一种未命名的事件使用 json 格式的数据::

    @socketio.on('json')
    def handle_json(json):
        print('received json: ' + str(json))

最灵活的事件类型使用自定义事件名称. 事件的消息数据可以为 string， bytes, int, or json::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))

自定义命名事件也可以支持多个参数::

    @socketio.on('my event')
    def handle_my_custom_event(arg1, arg2, arg3):
        print('received args: ' + arg1 + arg2 + arg3)


命名事件是最灵活的，因为他们不再需要包括元数据来描述消息类型.

Flask-SocketIO 也支持 SocketIO 的命名空间，它允许客户端多路复用与相同的物理 socket 建立几个独立的连接::

    @socketio.on('my event', namespace='/test')
    def handle_my_custom_namespace_event(json):
        print('received json: ' + str(json))

如果命名空间未指定，一个默认的全局的命名空间 ``'/'`` 将会被使用.

客户端可以请求确认回调以确认收到消息.
从处理函数返回的任何参数将会被传递到客户端的回调函数里::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))
        return 'one', 2

在上面的例子中，客户端的回调函数被调用时使用两个参数,``'one'`` 和 ``2``.
如果一个处理函数没有返回任何的值，客户端回调函数将会不带参数被调用.

Sending Messages
----------------

SocketIO 事件处理定义了在前一节中展示的可以在与连接的客户端中使用 ``send()`` 和 ``emit()`` 函数
来在发送和接收消息.

下面的例子返回接收的事件给他们的客户端::

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

注意 ``send()`` 和 ``emit()`` 分别在命名和未命名的事件中是如何发送的.

当使用命名空间时， ``send()`` 和 ``emit()`` 默认使用传入参数的命名空间.
可以通过选项 ``namespace`` 来指定一个不同的命名空间::

    @socketio.on('message')
    def handle_message(message):
        send(message, namespace='/chat')

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json, namespace='/chat')

要使用多个参数来发送一个事件，发送一个元组::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', ('foo', 'bar', json), namespace='/chat')

SocketIO 支持当消息被客户端接收的确认回调::

    def ack():
        print 'message was received!'

    @socketio.on('my event')
    def handle_my_custom_event(json):
        emit('my response', json, callback=ack)

When using callbacks the Javascript client receives a callback function to
invoke upon receipt of the message.
在客户端应用程序调用了回调函数后服务端调用想对应的服务端回调.
如果客户端回调返回任何值，他们将被作为参数传递给服务端的回调函数.

客户端应用程序也可以请求一个事件的确认回调然后发送给服务器.
如果服务器需要提供此回调的证据，就必须从事件处理函数返回他们::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        # ... handle the event

        return 'foo', 'bar', 123  # client callback will receive these 3 arguments

广播
------------

SocketIO 的另一个有用的功能是消息的广播.
Flask-SocketIO 也支持这个功能, 只需要给 ``send()`` 和 ``emit()`` 加上 ``broadcast=True`` 选项即可::


    @socketio.on('my event')
    def handle_my_custom_event(data):
        emit('my response', data, broadcast=True)

当一个消息被发送时开启了广播选项，所有连接到这个命名空间的客户端都将接收到这个消息，也包括发送端.
当没有使用命名空间时, 连接到全局命名空间的客户端将收到这些消息.
注意，在广播消息中回调将不会被调用.

所有的例子直到这一点都展示服务端响应由客户端发送的事件.
但是对于一些应用，服务器必须是消息的发起者.
这在给客户端发送起源与服务器的事件的通知是非常有用的,例如后台线程.

``socketio.send()`` 和 ``socketio.emit()`` 可以被用作广播到所有的连接的客户端上::

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

    @socketio.on('connect', namespace='/chat')
    def test_connect():
        emit('my response', {'data': 'Connected'})

    @socketio.on('disconnect', namespace='/chat')
    def test_disconnect():
        print('Client disconnected')

The connection event handler can optionally return ``False`` to reject the
connection. This is so that the client can be authenticated at this point.

Note that connection and disconnection events are sent individually on each
namespace used.

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

A common need of applications is to validate the identify of their users. The
traditional mechanisms based on web forms and HTTP requests cannot be used in
a SocketIO connection, since there is no place to send HTTP requests and
responses. If necessary, an application can implement a customized login form
that sends credentials to the server as a SocketIO message when the submit
button is pressed by the user.

However, in most cases it is more convenient to perform the traditional
authentication process before the SocketIO connection is established. The
user's identify can then be recorded in the user session or in a cookie, and
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
    from flask_socketio import disconnect

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

Gunicorn release 18.0 is the recommended release to use with Flask-SocketIO.
The 19.x releases are known to have incompatibilities in certain deployment
scenarios that include WebSocket.

Due to the limited load balancing algorithm used by gunicorn, it is not possible
to use more than one worker process when using this web server. For that reason,
all the examples above include the ``-w 1`` option.

uWSGI Web Server
~~~~~~~~~~~~~~~~

At this time, uWSGI is not a good choice of web server for a SocketIO
application due to the following limitations:

- The ``'eventlet'`` async mode cannot be used, as uWSGI currently does not
  support web servers based on eventlet.
- The ``'gevent'`` async mode is supported, but uWSGI is currently
  incompatible with the gevent-websocket package, so only the long-polling
  transport can be used.
- The native WebSocket support available from uWSGI is not based on eventlet
  or gevent, so it cannot be used at this time. If possible, a WebSocket
  transport based on the uWSGI WebSocket implementation will be made available
  in a future release.

Using nginx as a WebSocket Reverse Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to use nginx as a front-end reverse proxy that passes requests
to the application. However, only releases of nginx 1.4 and newer support
proxying of the WebSocket protocol. Below is an example nginx configuration
that proxies HTTP and WebSocket requests::

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
- For other message queues supported by Kombu, see the `Kombu documentation 
  <http://docs.celeryproject.org/projects/kombu/en/latest/introduction.html#transport-comparison>`_
  to find out what dependencies are needed.

To start multiple Flask-SocketIO servers, you must first ensure you have the
message queue service running. To start a Socket.IO server and have it connect to
the message queue, add the ``message_queue`` argument to the ``SocketIO``
constructor::

    socketio = SocketIO(app, message_queue='redis://')

The value of the ``message_queue`` argument is the connection URL of the
queue service that is used. For a redis queue running on the same host as the
server, the ``'redis://'`` URL can be used. Likewise, for a default RabbitMQ
queue the ``'amqp://'`` URL can be used. The Kombu package has a `documentation
section <http://docs.celeryproject.org/projects/kombu/en/latest/userguide/connections.html?highlight=urls#urls>`_
that describes the format of the URLs for all the supported queues.

Emitting from an External Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For many types of applications, it is necessary to emit events from a process
that is not the SocketIO server, for a example a Celery worker. If the
SocketIO server or servers are configured to listen on a message queue as
shown in the previous section, then any other process can create its own
``SocketIO`` instance and use it to emit events in the same way the server
does.

For example, for an application that runs on an eventlet web server and uses
a Redis message queue, the following Python script broadcasts an event to
all clients::

    import eventlet
    eventlet.monkey_patch()
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
