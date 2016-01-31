.. Flask-SocketIO documentation master file, created by
   sphinx-quickstart on Sun Feb  9 12:36:23 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

欢迎来到 Flask-SocketIO 中文文档!
===============================

Note: 初次尝试着翻译文档，以此来提升自己，但水平实在有限，也没有花过多的时间在上面，所以一些翻译不当的地方还请谅解，同时还希望有同胞愿意来改进，感激不尽。

**Flask-SocketIO** 使得 Flask 应用在服务端和客户端的双向通信中延迟更低。
客户端的应用程序可以使用任何Javascript，  C++, Java 和 Swift 的官方的客户端库，
或者其他任何官方的 `SocketIO <http://socket.io>`_ 客户端，
与服务端建立永久的链接。

安装
-------------------------------

你可以使用 ``pip`` 安装这个包：

    pip install flask-socketio

依赖
------------

自从 1.0 版本以来，这个扩展便支持 Python2.7 和 Python 3.3+ 了。
这个包所依赖的异步服务器可以从下面三个中任选其一即可:

- `eventlet <http://eventlet.net/>`_ 从性能上来说这是目前最好的选择，
  它支持长 long-polling 和 WebSocket transports。

- `gevent <http://www.gevent.org/>`_ 是 flask-socketio 早期版本使用的框架。
  long-polling 是完全支持的，但是如果要想支持 WebSocket，就必须将
  `gevent-websocket <https://pypi.python.org/pypi/gevent-websocket/>`_ 安装好。
  使用 gevent 和 gevent-websocket 性能也很不错，不过要比 eventlet 稍微低一点点。

- 基于 Werkzeug 的 Flask 开发服务器也可以被很好的使用，但是需要提醒的是，它的性能远不如其他两个可选方案，
  因此它应该仅用作来简化开发流程。这个选项仅支持long-polling transport。

flask-socketio 将根据你所安装的异步框架来自动选择，优先选择 eventlet，其次是 gevent。
如果这两个都没有被安装，将会使用 Flask 开发服务器。

如果使用多个进程，将使用一个消息队列来协调操作。
支持队列的有 `Redis <http://redis.io/>`_, `RabbitMQ <https://www.rabbitmq.com/>`_,
或者其他任何支持 `Kombu <http://kombu.readthedocs.org/en/latest/>`_ 包的消息队列。

在客户端，官方的 Socket.IO Javascript 客户端库可以用于建立与服务器的链接。
也有用 Swift， Java， C++ 写的官方客户端。非官方的客户端，只要实现了
`Socket.IO 协议 <https://github.com/socketio/socket.io-protocol>`_. 也行。


与 Flask-SocketIO 0.x 版本的差异
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

旧版本的 Flask-SocketIO 有着完全不同的依赖关系。
这些老版本依赖的
`gevent-socketio <https://gevent-socketio.readthedocs.org/en/latest/>`_ 和
`gevent-websocket <https://pypi.python.org/pypi/gevent-websocket/>`_, 在 1.0 版本都不再依赖。

尽管依赖关系有变化，但是在 1.0 版本中整体并没有什么显著的变化。
下面是实际的差异列表：

- 1.0 版本删除了对 Python 2.6 的支持， 并且添加了对 Python 3.3, Python 3.4 和 pypy 的支持。
- 使用 0.x 版本需要一个老版本的 Socket.IO Javascript 客户端。
  从 1.0 版本开始，可支持 Socket.IO 和 Engine.IO 最新的版本。
  还没有支持 Socket.IO 1.0 之前的版本。
  Swift 和 C++ 官方的 Socket.IO 客户端也可以很好的支持。
- 0.x 版本 依赖 gevent，gevent-socketio 和 gevent-websocket。
  在 1.0 版本中， 将不再使用 gevent-socketio,
  并且 gevent 是三个后端 web server 选项之一, 包括 eventlet 和任何常规的多线程 WSGI 服务器，以及 Flask 的开发服务器。
- Socket.IO 服务器选项已经在 1.0 版本更改。
  他们可以在 SocketIO 的构造函数中被提供，或者通过 ``run()`` 调用。
  这提供的两个选项在使用前已经被合并。
- 0.x 版本使用 ``request.namespace`` 暴露了 gevent-socketio 的连接。
  在 1.0 版本这些将不再可用。
  请求对象 ``request.namespace`` 作为命名空间被处理，并且添加了 ``request.sid``，
  定义为客户端链接会话的唯一id，并且 ``request.event`` 中包含了事件名称和参数。
- To get the list of rooms a client was in the 0.x release required the
  application to use a private structure of gevent-socketio, with the
  expression ``request.namespace.rooms``. This is not available in release
  1.0, which includes a proper ``rooms()`` function.
- 推荐的 "trick" 是，发送一条消息给一个客户端，是将客户端单独放到一个房间里，然后发送消息到这个房间.
  这就是 1.0 版本，当客户端连接时将自动分配给他们一个房间。
- The ``'connect'`` event for the global namespace did not fire on releases
  prior to 1.0. This has been fixed and now this event fires as expected.
- Support for client-side callbacks was introduced in release 1.0.

将 Flask-SocketIO 从更早的版本升级到 1.x 和 2.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在客户端上，你需要去升级你的 Socket.IO Javascript 客户端 到 1.3.x 或者更新版本。

在客户端，有一些需要考虑的地方：

- 如果你希望继续使用 gevent， 然后你需要从你的虚拟环境中卸载 gevent-socketio ，
  因为不再使用该软件包，并且可能与他的替代软件包 python-socketio 发生冲突。
- 如果你希望有个较好的性能和稳定性，建议你切换到 eventlet。 为了做到这一点，
  卸载 gevent， gevent-socketio 和 gevent-websocket, 然后再安装 eventlet。
- 如果你的应用使用 monkey patching 并且你已经切换到了 eventlet, 调用 `eventlet.monkey_patch()`
  替代 gevent 的 `monkey.patch_all()` 。 此外，任何调用 gevent 都必须替换成调用(或相当与调用) eventlet。
- 任何使用 `request.namespace` 都必须替换成直接调用 Flask-SocketIO 的方法。
  例如，`request.namespace.rooms` 必须替换成 Flask-SocketIO 的 `rooms()` 方法.
- 内部的任何 gevent-socketio 对象都必须移除, 因为已经不再依赖与这个包了。

安装
--------------

下面的代码演示了如何添加 Flask-SocketIO 到一个 Flask 应用中::

    from flask import Flask, render_template
    from flask_socketio import SocketIO

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)

    if __name__ == '__main__':
        socketio.run(app)

同样也支持 ``init_app()`` 的初始化风格。 注意这个 web server 启动的方法。
``socketio.run()`` 封装了 web server 的启动并且替代了 Flask 开发环境标准的启动方式 ``app.run()`` 。
当应用在 debug 模式下，Werkzeug 开发服务器依然在使用并且在 ``socketio.run()`` 内部已经正确配置。
在生产环境中，如果 eventlet 可用的话将使用 eventlet， 否则将会使用 gevent 。
如果 eventlet 和 gevent 都没有被安装, 将使用 Werkzeug 的开发服务器。

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

当使用 SocketIO时, 接收消息是双向的事件。在客户端将使用 Javascript 回调。
使用 Flask-SocketIO 服务端需要注册这些事件的处理，类似与视图函数处理路由一样。

下面的示例为一个没有定义的事件创建了一个服务端事件处理::

    @socketio.on('message')
    def handle_message(message):
        print('received message: ' + message)

上面的例子使用字符串消息。 另一种未命名的事件使用 json 格式的数据::

    @socketio.on('json')
    def handle_json(json):
        print('received json: ' + str(json))

最灵活的事件类型是使用自定义事件名称，事件的消息数据类型可以为 string， bytes, int, 或者 json::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))

自定义命名事件也可以支持多个参数::

    @socketio.on('my event')
    def handle_my_custom_event(arg1, arg2, arg3):
        print('received args: ' + arg1 + arg2 + arg3)


自定义命名事件是最灵活的，因为他们不再需要包含元数据来描述消息类型。
Flask-SocketIO 也支持 SocketIO 的命名空间，它允许客户端多路复用，与相同的物理 socket 建立几个独立的连接::

    @socketio.on('my event', namespace='/test')
    def handle_my_custom_namespace_event(json):
        print('received json: ' + str(json))

如果命名空间未指定，将会使用一个默认的全局命名空间 ``'/'`` 。
客户端可以请求确认回调来确认收到消息。
从处理函数返回的任何参数都将会被传递到客户端的回调函数里::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))
        return 'one', 2

在上面的例子中，客户端的回调函数被调用时使用两个参数,``'one'`` 和 ``2``。
如果一个处理函数没有返回任何的值，客户端回调函数将会不带参数被调用。

发送消息
----------------

SocketIO 事件处理定义了在前一节中展示的可以在与连接的客户端中使用 ``send()`` 和 ``emit()`` 函数
来在发送和接收消息。

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

注意观察 ``send()`` 和 ``emit()`` 分别在命名和未命名的事件中是如何发送的。

当使用命名空间时， ``send()`` 和 ``emit()`` 默认使用传入参数的命名空间。
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
在客户端应用程序调用了回调函数后服务端调用相对应的服务端回调函数。
如果客户端回调返回了任何值，他们将被作为参数传递给服务端的回调函数。

客户端应用程序也可以请求一个事件的确认回调然后发送给服务器。
如果服务器需要提供此回调的证据，就必须从事件处理函数返回他们::

    @socketio.on('my event')
    def handle_my_custom_event(json):
        # ... handle the event

        return 'foo', 'bar', 123  # client callback will receive these 3 arguments

广播
------------

SocketIO 的另一个有用的功能是消息广播。
Flask-SocketIO 也支持这个功能, 只需要给 ``send()`` 和 ``emit()`` 加上 ``broadcast=True`` 选项即可::


    @socketio.on('my event')
    def handle_my_custom_event(data):
        emit('my response', data, broadcast=True)

当一个消息被发送时开启了广播选项，所有连接到这个命名空间的客户端都将接收到这条消息，也包括发送端。
当没有使用命名空间时, 连接到全局命名空间的客户端将收到这些消息。
注意，在广播消息中回调将不会被调用。

在这以前的所有的例子都演示服务端响应由客户端发送的事件。
但是对于一些应用，服务器必须是消息的发起者。
这在给客户端发送给起源与服务器的事件的通知是非常有用的,例如后台线程。

``socketio.send()`` 和 ``socketio.emit()`` 可以被用作广播到所有的连接的客户端上::

    def some_function():
        socketio.emit('some event', {'data': 42})

Note that ``socketio.send()`` and ``socketio.emit()`` are not the same
functions as the context-aware ``send()`` and ``emit()``. Also note that in the
above usage there is no client context, so ``broadcast=True`` is assumed and
does not need to be specified.

房间
-----

对很多应用来说，把用户分组是非常有必要的，以便可以统一处理。
最好的例子就是，一个聊天应用有多个房间，用户可以从一个房间或他们所在的其他房间接收消息，
但是不能从其他用户所在的房间那里接收消息。
Flask-SocketIO 通过 ``join_room()`` 和 ``leave_room()`` 来支持房间的概念::

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

``send()`` 和 ``emit()`` 函数接收一个可选的 ``room`` 参数来使得消息被发送到指定房间的所有客户端。

每一个连接都会被自动分配到一个房间，这个房间以连接的会话ID命名，可以通过 ``request.sid`` 获取到。
一个给定的客户端可以加入到任何名称的任何房间。
当一个客户端断开时，他将被所有的房间移除。
与上下文无关的 ``socketio.send()`` 和 ``socketio.emit()`` 也接收一个 ``room`` 参数
来广播给一个房间的所有客户端。

所有的客户端都会默认被分配到一个人单独在一个房间，以处理发送给单个客户端的消息，
客户端的会话ID可以被用作房间的参数。

连接事件
-----------------

Flask-SocketIO 还可以调度连接和断开事件。
下面的例子展示了如何注册处理它们::

    @socketio.on('connect', namespace='/chat')
    def test_connect():
        emit('my response', {'data': 'Connected'})

    @socketio.on('disconnect', namespace='/chat')
    def test_disconnect():
        print('Client disconnected')

连接处理程序可以选择返回 ``False`` 来拒绝连接。
所以，客户端可以在此时进行验证。

需要注意的是，连接和断开事件会被发送到每一个被使用的命名空间。

错误处理
--------------

Flask-SocketIO 也可以处理异常::

    @socketio.on_error()        # 处理默认的命名空间
    def error_handler(e):
        pass

    @socketio.on_error('/chat') # 处理 '/chat' 命名空间
    def error_handler_chat(e):
        pass

    @socketio.on_error_default  # 处理所有命名空间中不明确的错误处理
    def default_error_handler(e):
        pass

错误处理函数把异常的对象作为参数。

当前请求的消息和数据参数可以通过 ``request.event`` 变量查看。
这对事件处理程序之外的错误日志记录和调试很有用::

    from flask import request

    @socketio.on("my error event")
    def on_my_event(data):
        raise RuntimeError()

    @socketio.on_error_default
    def default_error_handler(e):
        print(request.event["message"]) # "my error event"
        print(request.event["args"])    # (data,)

允许 Flask 访问全局上下文
---------------------------------

处理 SocketIO 事件与处理路由是不同的,主要是因为一个 SocketIO 事件围绕能做什么和不能做什么引入了很多混乱的东西。
主要的区别是，客户端生成的所有 SocketIO 事件都是一个单一的长链接。

尽管有区别， Flask-SocketIO 尝试使得处理 SocketIO 事件与类似处理常规的HTTP请求一样容易。
下面的列表说明了什么可行什么不可行:

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

认证
--------------

应用程序的共同需求是验证和识别他们的用户。基于 web 形式和传统的 HTTP 请求的方式无法在 SocketIO 连接中使用,
因为没有地方来发送 HTTP 请求及响应。如果有必要的话，一个应用程序可以实现一个专门的表单，
当用户按下提交按钮后来发送凭证给服务器。

然而，在大多数情况下，在进行 SocketIO 连接之前进行传统的认证处理是非常方便的。
认证后的用户标识可以存储在用户的会话或者 cookie 中,在之后的请求中，
当 SocketIO 连接是已认证通过的情况下，请求将会允许被 SocketIO 事件处理。

与 Flask-Login 一起使用 Flask-SocketIO
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flask-SocketIO 可以访问由 `Flask-Login <https://flask-login.readthedocs.org/en/latest/>`_ 提供的登录信息。
在经过 Flask-Login 的认证处理之后, ``login_user()`` 函数会被调用，来记录用户到用户会话中,
并且 SocketIO 会有权限访问上下文变量 ``current_user``::


    @socketio.on('connect')
    def connect_handler():
        if current_user.is_authenticated:
            emit('my response',
                 {'message': '{0} has joined'.format(current_user.name)},
                 broadcast=True)
        else:
            return False  # not allowed here

需要注意的是 ``login_required`` 装饰器不能与 SocketIO 事件处理程序一起使用,
但可以用如下的方法来创建一个自定义的装饰器来断开未经认证的用户::

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

部署
----------

从简单到复杂，有很多种选项来部署一个 Flask-SocketIO 服务器。
在本教程中，选用最常用的选择来进行说明。

嵌入式服务器
~~~~~~~~~~~~~~~

最见的部署策略是安装 eventlet 或者 gevent 。并通过调用在前面的例子中提到过的
``socketio.run(app)`` 来启动 web 服务器。
这将把应用运行在 eventlet 和 gevent 中的一个(取决与系统中安装了哪一个)。

需要注意的是， ``socketio.run(app)`` 在当 eventlet 或者 gevent 已安装的情况下会运行一个生产环境的服务器。
如果两者都没有安装，应用程序将会运行在 Flask 的开发服务器之上, 这非常不适合用与生产环境。

Gunicorn Web 服务器
~~~~~~~~~~~~~~~~~~~

除了 ``socketio.run(app)`` 的另一种启动方式是使用
`gunicorn <http://gunicorn.org/>`_ 作为一个 Web 服务器, 需要使用 eventlet 或者 gevent workers。
对于这个选项， eventlet 或者 gevent 必须要安装一个，此外还有 gunicorn 。
下面是在命令行中通过 gunicorn 启动 eventlet 服务器的命令::

    gunicorn --worker-class eventlet -w 1 module:app

如果你喜欢使用 gevent 来启动服务器，命令如下所示::

    gunicorn -k gevent -w 1 module:app

当使用 gunicorn 与 gevent 一起工作时，WebSocket 将由 gevent-websocket 提供支持。
启动服务器的命令必须改变,以选择支持自定义的 WebSocket 协议的 web 服务器。
命令修改如下::

    gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 module:app

在上面这些例子中, ``module`` 是 Python 在应用实例中定义的模块或者包,
``app`` 是这个应用实例自身。

18.0 版本的 Gunicorn 建议和 Flask-SocketIO 一起使用, 但在 19.x 的版本中已知了一些
包括 WebSocket 在内的一些不兼容情况。

由于 gunicorn 有限的负载均衡算法，当使用此 web 服务器是不可能有一个以上的工作进程的。
出于这个原因，上面的例子都包含了 ``-w 1`` 选项。

uWSGI Web 服务器
~~~~~~~~~~~~~~~~

此时， 对于一个 SocketIO 应用程序来说，uWSGI 不是一个很好的选择，因为它有如下限制:

- ``'eventlet'`` 的异步模式不能使用，因为 uWSGI 目前不支持基于 eventlet 的 web 服务器。
- 支持 ``'gevent'`` 异步模式，但是 uWSGI 当前与 gevent-websocket 包不兼容，
  所以仅仅可以使用长轮询传输。
- uWSGI 本身支持不基于 eventlet 和 gevent 的 WebSocket,所以它在这个时候不能被使用。
  如果可能的话，基于 uWSGI 的 WebSocket 会在以后的版本中提供。

使用 nginx 作为一个 WebSocket 的反向代理
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

可以使用 nginx 作为一个前端的反向代理来将请求传递给应用程序。
然而，仅仅 nginx 1.4 或者更新的版本才支持代理 WebSocket 协议。
下面是一个 nginx 代理 HTTP 和 WebSocket 请求的实例配置::

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
Flask-SocketIO 将在 2.0 版本中支持在多个进程之间实现负载均衡。
部署多个进程使得使用 Flask-SocketIO 的应用在连接多个主机和客户端上有更高的能力,
这非常适合高并发的场合。

使用 Flask-SocketIO 的多进程有两个要求:

- 负载均衡器必须配置成同一个客户端的所有请求都转发到相同的 worker 。  这被称为"sticky sessions"。
  对于nginx来说,使用 ``ip_hash`` 来实现这一目标。 Gunicorn 不能使用多个工作线程，
  因为它的负载均衡器不支持 sticky sessions。
- 因为每个服务器仅仅拥有所有客户端连接的一个子集，一个消息队列如 Redis 或者 RabbitMQ 服务器
  可以协助诸如广播和"房间"等一些复杂的操作。

当使用消息队列工作时，需要额外的安装一些依赖:

- 对于 Redis， ``redis`` 包必须要安装 (``pip install redis``)。
- 对于 RabbitMQ， ``kombu`` 包必须安装 (``pip install kombu``)。
- 对于 Kombu 支持的其他消息队列， 可以从 `Kombu documentation
  <http://docs.celeryproject.org/projects/kombu/en/latest/introduction.html#transport-comparison>`_
  找到他们对应的依赖。

要启动多个 Flask-SocketIO 服务器， 你必须首先确保你有消息队列在运行。
启动 Socket.IO 服务器并且让它连接到消息队列,添加 ``message_queue`` 参数到 ``SocketIO`` 构造中::

    socketio = SocketIO(app, message_queue='redis://')

``message_queue`` 参数的值是用作队列服务的连接地址。 对于 Redis 队列来说，
如果运行在同一台服务器的话，默认可以使用 ``'redis://'`` 。
同样，对于默认的 RabbitMQ 也可以使用 ``'amqp://'`` 。 Kombu 包包含了一个
`documentation section <http://docs.celeryproject.org/projects/kombu/en/latest/userguide/connections.html?highlight=urls#urls>`_ ，
它描述了所有支持队列的URL格式。

Emitting from an External Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For many types of applications, it is necessary to emit events from a process
that is not the SocketIO server, for a example a Celery worker. If the
SocketIO server or servers are configured to listen on a message queue as
shown in the previous section, then any other process can create its own
``SocketIO`` instance and use it to emit events in the same way the server
does.

例如， 对于一个运行在 eventlet web 服务器和 Redis 消息队列的应用来说，下面的 Python
脚本广播了一个事件给所有客户端::

    import eventlet
    eventlet.monkey_patch()
    socketio = SocketIO(message_queue='redis://')
    socketio.emit('my event', {'data': 'foo'}, namespace='/test')

当以这种方式来使用 ``SocketIO`` 实例时，Flask 应用程序的实例没有传递给构造。

``SocketIO`` 的 ``channel`` 参数可以用来在消息队列中选择一个特殊的通道。
使用自定义的频道名称时， 多个独立的 SocketIO 服务共用一个消息队列是非常有必要的。

Flask-SocketIO 使用 eventlet 或者 gevent 时将不能使用猴子补丁。
但是，当使用消息队列时，如果 Python 标准库不是猴子补丁，那消息队列服务将会被挂起是非常有可能的。

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
