import os
import sys
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

if sys.version_info >= (3, 5):
    import asyncio
    from engineio.async_drivers import asgi as async_asgi


def AsyncMock(*args, **kwargs):
    """Return a mock asynchronous function."""
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class AsgiTests(unittest.TestCase):
    def test_create_app(self):
        app = async_asgi.ASGIApp(
            'eio', 'other_app', static_files='static_files',
            engineio_path='/foo')
        self.assertEqual(app.engineio_server, 'eio')
        self.assertEqual(app.other_asgi_app, 'other_app')
        self.assertEqual(app.static_files, 'static_files')
        self.assertEqual(app.engineio_path, 'foo'),

    def test_engineio_routing(self):
        mock_server = mock.MagicMock()
        mock_server.handle_request = AsyncMock()
        app = async_asgi.ASGIApp(mock_server)
        scope = {'type': 'http', 'path': '/engine.io/'}
        handler = app(scope)
        _run(handler('receive', 'send'))
        mock_server.handle_request.mock.assert_called_once_with(
            scope, 'receive', 'send')

    def test_other_app_routing(self):
        other_app = mock.MagicMock()
        app = async_asgi.ASGIApp('eio', other_app)
        scope = {'type': 'http', 'path': '/foo'}
        app(scope)
        other_app.assert_called_once_with(scope)

    def test_static_file_routing(self):
        root_dir = os.path.dirname(__file__)
        app = async_asgi.ASGIApp('eio', static_files={
            '/foo': {'content_type': 'text/html',
                     'filename': root_dir + '/index.html'}
        })
        handler = app({'type': 'http', 'path': '/foo'})
        receive = AsyncMock(return_value={'type': 'http.request'})
        send = AsyncMock()
        _run(handler(receive, send))
        send.mock.assert_called_with({'type': 'http.response.body',
                                      'body': b'<html></html>\n'})

    def test_lifespan_startup(self):
        app = async_asgi.ASGIApp('eio')
        handler = app({'type': 'lifespan'})
        receive = AsyncMock(return_value={'type': 'lifespan.startup'})
        send = AsyncMock()
        _run(handler(receive, send))
        send.mock.assert_called_once_with(
            {'type': 'lifespan.startup.complete'})

    def test_lifespan_shutdown(self):
        app = async_asgi.ASGIApp('eio')
        handler = app({'type': 'lifespan'})
        receive = AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = AsyncMock()
        _run(handler(receive, send))
        send.mock.assert_called_once_with(
            {'type': 'lifespan.shutdown.complete'})

    def test_lifespan_invalid(self):
        app = async_asgi.ASGIApp('eio')
        handler = app({'type': 'lifespan'})
        receive = AsyncMock(return_value={'type': 'lifespan.foo'})
        send = AsyncMock()
        _run(handler(receive, send))
        send.mock.assert_not_called()

    def test_not_found(self):
        app = async_asgi.ASGIApp('eio')
        handler = app({'type': 'http', 'path': '/foo'})
        receive = AsyncMock(return_value={'type': 'http.request'})
        send = AsyncMock()
        _run(handler(receive, send))
        send.mock.assert_any_call(
            {'type': 'http.response.start', 'status': 404,
             'headers': [(b'Content-Type', b'text/plain')]})
        send.mock.assert_any_call({'type': 'http.response.body',
                                   'body': b'not found'})

    def test_translate_request(self):
        receive = AsyncMock(return_value={'type': 'http.request',
                                          'body': b'hello world'})
        send = AsyncMock()
        environ = _run(async_asgi.translate_request({
            'type': 'http',
            'method': 'PUT',
            'headers': [(b'a', b'b'), (b'c-c', b'd'), (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123')],
            'path': '/foo/bar',
            'query_string': b'baz=1'}, receive, send))
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': '123',
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'asgi.receive': receive,
            'asgi.send': send
        }
        for k, v in expected_environ.items():
            self.assertEqual(v, environ[k])
        self.assertTrue(
            environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d')
        body = _run(environ['wsgi.input'].read())
        self.assertEqual(body, b'hello world')

    def test_translate_request_no_query_string(self):
        receive = AsyncMock(return_value={'type': 'http.request',
                                          'body': b'hello world'})
        send = AsyncMock()
        environ = _run(async_asgi.translate_request({
            'type': 'http',
            'method': 'PUT',
            'headers': [(b'a', b'b'), (b'c-c', b'd'), (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123')],
            'path': '/foo/bar'}, receive, send))
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': '123',
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'asgi.receive': receive,
            'asgi.send': send
        }
        for k, v in expected_environ.items():
            self.assertEqual(v, environ[k])
        self.assertTrue(
            environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d')
        body = _run(environ['wsgi.input'].read())
        self.assertEqual(body, b'hello world')

    def test_translate_request_with_large_body(self):
        receive = AsyncMock(side_effect=[
            {'type': 'http.request', 'body': b'hello ', 'more_body': True},
            {'type': 'http.request', 'body': b'world', 'more_body': True},
            {'type': 'foo.bar'},  # should stop parsing here
            {'type': 'http.request', 'body': b'!!!'},
        ])
        send = AsyncMock()
        environ = _run(async_asgi.translate_request({
            'type': 'http',
            'method': 'PUT',
            'headers': [(b'a', b'b'), (b'c-c', b'd'), (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123')],
            'path': '/foo/bar',
            'query_string': b'baz=1'}, receive, send))
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': '123',
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'asgi.receive': receive,
            'asgi.send': send
        }
        for k, v in expected_environ.items():
            self.assertEqual(v, environ[k])
        self.assertTrue(
            environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d')
        body = _run(environ['wsgi.input'].read())
        self.assertEqual(body, b'hello world')

    def test_translate_websocket_request(self):
        receive = AsyncMock(return_value={'type': 'websocket.connect'})
        send = AsyncMock()
        _run(async_asgi.translate_request({
            'type': 'websocket',
            'headers': [(b'a', b'b'), (b'c-c', b'd'), (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123')],
            'path': '/foo/bar',
            'query_string': b'baz=1'}, receive, send))
        send.mock.assert_called_once_with({'type': 'websocket.accept'})

    def test_translate_unknown_request(self):
        receive = AsyncMock(return_value={'type': 'http.foo'})
        send = AsyncMock()
        environ = _run(async_asgi.translate_request({
            'type': 'http',
            'path': '/foo/bar',
            'query_string': b'baz=1'}, receive, send))
        self.assertEqual(environ, {})

    # @mock.patch('async_aiohttp.aiohttp.web.Response')
    def test_make_response(self):
        environ = {
            'asgi.send': AsyncMock()
        }
        _run(async_asgi.make_response('202 ACCEPTED', [('foo', 'bar')],
                                      b'payload', environ))
        environ['asgi.send'].mock.assert_any_call(
            {'type': 'http.response.start', 'status': 202,
             'headers': [(b'foo', b'bar')]})
        environ['asgi.send'].mock.assert_any_call(
            {'type': 'http.response.body', 'body': b'payload'})
