try:
    import asyncio
except ImportError:
    pass
import sys
import unittest

import six
try:
    import tornado.web
except ImportError:
    pass
if six.PY3:
    from unittest import mock
else:
    import mock

if sys.version_info >= (3, 5):
    from engineio.async_drivers import tornado as async_tornado


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class TornadoTests(unittest.TestCase):
    def test_get_tornado_handler(self):
        mock_server = mock.MagicMock()
        handler = async_tornado.get_tornado_handler(mock_server)
        self.assertTrue(issubclass(handler,
                                   tornado.websocket.WebSocketHandler))

    def test_translate_request(self):
        mock_handler = mock.MagicMock()
        mock_handler.request.method = 'PUT'
        mock_handler.request.path = '/foo/bar'
        mock_handler.request.query = 'baz=1'
        mock_handler.request.version = '1.1'
        mock_handler.request.headers = {
            'a': 'b',
            'c': 'd',
            'content-type': 'application/json',
            'content-length': 123
        }
        mock_handler.request.body = b'hello world'
        environ = async_tornado.translate_request(mock_handler)
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': 123,
            'HTTP_A': 'b',
            'HTTP_C': 'd',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            # 'wsgi.input': b'hello world',
            'tornado.handler': mock_handler,
        }
        for k, v in expected_environ.items():
            self.assertEqual(v, environ[k])
        payload = _run(environ['wsgi.input'].read(1))
        payload += _run(environ['wsgi.input'].read())
        self.assertEqual(payload, b'hello world')

    def test_make_response(self):
        mock_handler = mock.MagicMock()
        mock_environ = {'tornado.handler': mock_handler}
        async_tornado.make_response('202 ACCEPTED', [('foo', 'bar')],
                                    b'payload', mock_environ)
        mock_handler.set_status.assert_called_once_with(202)
        mock_handler.set_header.assert_called_once_with('foo', 'bar')
        mock_handler.write.assert_called_once_with(b'payload')
        mock_handler.finish.assert_called_once_with()
