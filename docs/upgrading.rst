Upgrading to Flask-SocketIO 5.x from the 4.x releases
-----------------------------------------------------

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
