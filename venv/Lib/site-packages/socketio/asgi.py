import engineio


class ASGIApp(engineio.ASGIApp):  # pragma: no cover
    """ASGI application middleware for Socket.IO.

    This middleware dispatches traffic to an Socket.IO application. It can
    also serve a list of static files to the client, or forward unrelated
    HTTP traffic to another ASGI application.

    :param socketio_server: The Socket.IO server. Must be an instance of the
                            ``socketio.AsyncServer`` class.
    :param static_files: A dictionary where the keys are URLs that should be
                         served as static files. For each URL, the value is
                         a dictionary with ``content_type`` and ``filename``
                         keys. This option is intended to be used for serving
                         client files during development.
    :param other_asgi_app: A separate ASGI app that receives all other traffic.
    :param socketio_path: The endpoint where the Socket.IO application should
                          be installed. The default value is appropriate for
                          most cases.

    Example usage::

        import socketio
        import uvicorn

        eio = socketio.AsyncServer()
        app = engineio.ASGIApp(eio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'index.html'},
            '/index.html': {'content_type': 'text/html',
                            'filename': 'index.html'},
        })
        uvicorn.run(app, '127.0.0.1', 5000)
    """
    def __init__(self, socketio_server, other_asgi_app=None,
                 static_files=None, socketio_path='socket.io'):
        super().__init__(socketio_server, other_asgi_app,
                         static_files=static_files,
                         engineio_path=socketio_path)
