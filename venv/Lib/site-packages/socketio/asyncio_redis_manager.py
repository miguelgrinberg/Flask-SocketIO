import asyncio
import pickle
from urllib.parse import urlparse

try:
    import aioredis
except ImportError:
    aioredis = None

from .asyncio_pubsub_manager import AsyncPubSubManager


def _parse_redis_url(url):
    p = urlparse(url)
    if p.scheme != 'redis':
        raise ValueError('Invalid redis url')
    host = p.hostname or 'localhost'
    port = p.port or 6379
    password = p.password
    if p.path:
        db = int(p.path[1:])
    else:
        db = 0
    return host, port, password, db


class AsyncRedisManager(AsyncPubSubManager):  # pragma: no cover
    """Redis based client manager for asyncio servers.

    This class implements a Redis backend for event sharing across multiple
    processes. Only kept here as one more example of how to build a custom
    backend, since the kombu backend is perfectly adequate to support a Redis
    message queue.

    To use a Redis backend, initialize the :class:`Server` instance as
    follows::

        server = socketio.Server(client_manager=socketio.AsyncRedisManager(
            'redis://hostname:port/0'))

    :param url: The connection URL for the Redis server. For a default Redis
                store running on the same host, use ``redis://``.
    :param channel: The channel name on which the server sends and receives
                    notifications. Must be the same in all the servers.
    :param write_only: If set ot ``True``, only initialize to emit events. The
                       default of ``False`` initializes the class for emitting
                       and receiving.
    """
    name = 'aioredis'

    def __init__(self, url='redis://localhost:6379/0', channel='socketio',
                 write_only=False, logger=None):
        if aioredis is None:
            raise RuntimeError('Redis package is not installed '
                               '(Run "pip install aioredis" in your '
                               'virtualenv).')
        self.host, self.port, self.password, self.db = _parse_redis_url(url)
        self.pub = None
        self.sub = None
        super().__init__(channel=channel, write_only=write_only, logger=logger)

    async def _publish(self, data):
        retry = True
        while True:
            try:
                if self.pub is None:
                    self.pub = await aioredis.create_redis(
                        (self.host, self.port), db=self.db,
                        password=self.password)
                return await self.pub.publish(self.channel,
                                              pickle.dumps(data))
            except (aioredis.RedisError, OSError):
                if retry:
                    self._get_logger().error('Cannot publish to redis... '
                                             'retrying')
                    self.pub = None
                    retry = False
                else:
                    self._get_logger().error('Cannot publish to redis... '
                                             'giving up')
                    break

    async def _listen(self):
        retry_sleep = 1
        while True:
            try:
                if self.sub is None:
                    self.sub = await aioredis.create_redis(
                        (self.host, self.port), db=self.db,
                        password=self.password)
                self.ch = (await self.sub.subscribe(self.channel))[0]
                return await self.ch.get()
            except (aioredis.RedisError, OSError):
                self._get_logger().error('Cannot receive from redis... '
                                         'retrying in '
                                         '{} secs'.format(retry_sleep))
                self.sub = None
                await asyncio.sleep(retry_sleep)
                retry_sleep *= 2
                if retry_sleep > 60:
                    retry_sleep = 60
