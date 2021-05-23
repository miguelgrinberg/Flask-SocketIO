Introduction
============

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
  caveat that this web server is intended only for development use, so it
  should only be used to simplify the development workflow and not for
  production.

The extension automatically detects which asynchronous framework to use based
on what is installed. Preference is given to eventlet, followed by gevent.
For WebSocket support in gevent, uWSGI is preferred, followed by
gevent-websocket. If neither eventlet nor gevent are installed, then the Flask
development server is used.

If using multiple processes, a message queue service must be configured to
allow the servers to coordinate operations such as broadcasting. The supported
queues are `Redis <http://redis.io/>`_, `RabbitMQ <https://www.rabbitmq.com/>`_,
`Kafka <http://kafka.apache.org/>`_, and any other message queues supported by
the `Kombu <http://kombu.readthedocs.org/en/latest/>`_ package.

On the client-side, the official Socket.IO Javascript client library can be
used to establish a connection to the server. There are also official clients
written in Swift, Java and C++. Unofficial clients may also work, as long as
they implement the
`Socket.IO protocol <https://github.com/socketio/socket.io-protocol>`_.
The `python-socketio <https://github.com/miguelgrinberg/python-socketio>`_
package (which provides the Socket.IO server implementation used by
Flask-SocketIO) includes a Python client.

Version compatibility
---------------------

The Socket.IO protocol has been through a number of revisions, and some of these
introduced backward incompatible changes, which means that the client and the
server must use compatible versions for everything to work.

The version compatibility chart below maps versions of this package to versions
of the JavaScript reference implementation and the versions of the Socket.IO and
Engine.IO protocols.

+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+-------------------------+
| JavaScript Socket.IO version | Socket.IO protocol revision | Engine.IO protocol revision | Flask-SocketIO version | python-socketio version | python-engineio version |
+==============================+=============================+=============================+========================+=========================+=========================+
| 0.9.x                        | 1, 2                        | 1, 2                        | Not supported          | Not supported           | Not supported           |
+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+-------------------------+
| 1.x and 2.x                  | 3, 4                        | 3                           | 4.x                    | 4.x                     | 3.x                     |
+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+-------------------------+
| 3.x and 4.x                  | 5                           | 4                           | 5.x                    | 5.x                     | 4.x                     |
+------------------------------+-----------------------------+-----------------------------+------------------------+-------------------------+-------------------------+
