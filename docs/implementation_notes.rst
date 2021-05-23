Implementation Notes
====================

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

Recent revisions of the Socket.IO protocol include the ability to pass a
dictionary with authentication information during the connection. This is an
ideal place for the client to include a token or other authentication details.
If the client uses this capability, the server will provide this dictionary as
an argument to the ``connect`` event handler, as shown above.


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
