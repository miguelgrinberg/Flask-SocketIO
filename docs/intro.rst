Introduction
============

Installation
------------

You can install this package in the usual way using ``pip``::

    pip install flask-socketio

Requirements
------------

Flask-SocketIO is compatible with Python 3.8+. The asynchronous services that
this package relies on can be selected among three choices:

- The ``threading`` package from the Python standard library is the easier and
  most compatible solution, with full support of long-polling and WebSocket
  transports. The Flask development web server can be used during development,
  and Gunicorn in multi-threaded mode can be used in production deployments.
- `gevent <http://www.gevent.org/>`_ is supported in a number of different
  configurations, also with support for the long-polling and WebSocket
  transports. The Flask development web server, gevent's own web server,
  Gunicorn (with the gevent worker) and uWSGI (in gevent mode) are all
  supported when using ``gevent``.
- `eventlet <http://eventlet.net/>`_ used to be a good option with support for
  long-polling and WebSocket transports, but it is not actively maintained
  anymore, so ``gevent`` should be preferred. The Flask development web server,
  eventlet's own web server and Gunicorn (with the eventlet worker) are all
  supported when using ``eventlet``.

The extension automatically detects which asynchronous framework to use based
on what is installed. Preference is given to eventlet, followed by gevent. If
neither eventlet nor gevent are installed, Python's ``threading`` package is
used.

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
