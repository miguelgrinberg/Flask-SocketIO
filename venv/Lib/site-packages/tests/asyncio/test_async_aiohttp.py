import sys
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

if sys.version_info >= (3, 5):
    from engineio.async_drivers import aiohttp as async_aiohttp


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class AiohttpTests(unittest.TestCase):
    def test_create_route(self):
        app = mock.MagicMock()
        mock_server = mock.MagicMock()
        async_aiohttp.create_route(app, mock_server, '/foo')
        app.router.add_get.assert_any_call('/foo', mock_server.handle_request)
        app.router.add_post.assert_any_call('/foo', mock_server.handle_request)

    def test_translate_request(self):
        request = mock.MagicMock()
        request._message.method = 'PUT'
        request._message.path = '/foo/bar?baz=1'
        request._message.version = (1, 1)
        request._message.headers = {'a': 'b', 'c-c': 'd', 'c_c': 'e',
                                    'content-type': 'application/json',
                                    'content-length': 123}
        request._payload = b'hello world'
        environ = async_aiohttp.translate_request(request)
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': 123,
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.input': b'hello world',
            'aiohttp.request': request,
        }
        for k, v in expected_environ.items():
            self.assertEqual(v, environ[k])
        self.assertTrue(
            environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d')

    # @mock.patch('async_aiohttp.aiohttp.web.Response')
    def test_make_response(self):
        rv = async_aiohttp.make_response('202 ACCEPTED', {'foo': 'bar'},
                                         b'payload', {})
        self.assertEqual(rv.status, 202)
        self.assertEqual(rv.headers['foo'], 'bar')
        self.assertEqual(rv.body, b'payload')
