import pickle
import uuid

try:
    import kombu
except ImportError:
    kombu = None

from .pubsub_manager import PubSubManager


class KombuManager(PubSubManager):  # pragma: no cover
    """Client manager that uses kombu for inter-process messaging.

    This class implements a client manager backend for event sharing across
    multiple processes, using RabbitMQ, Redis or any other messaging mechanism
    supported by `kombu <http://kombu.readthedocs.org/en/latest/>`_.

    To use a kombu backend, initialize the :class:`Server` instance as
    follows::

        url = 'amqp://user:password@hostname:port//'
        server = socketio.Server(client_manager=socketio.KombuManager(url))

    :param url: The connection URL for the backend messaging queue. Example
                connection URLs are ``'amqp://guest:guest@localhost:5672//'``
                and ``'redis://localhost:6379/'`` for RabbitMQ and Redis
                respectively. Consult the `kombu documentation
                <http://kombu.readthedocs.org/en/latest/userguide\
                /connections.html#urls>`_ for more on how to construct
                connection URLs.
    :param channel: The channel name on which the server sends and receives
                    notifications. Must be the same in all the servers.
    :param write_only: If set ot ``True``, only initialize to emit events. The
                       default of ``False`` initializes the class for emitting
                       and receiving.
    """
    name = 'kombu'

    def __init__(self, url='amqp://guest:guest@localhost:5672//',
                 channel='socketio', write_only=False, logger=None):
        if kombu is None:
            raise RuntimeError('Kombu package is not installed '
                               '(Run "pip install kombu" in your '
                               'virtualenv).')
        super(KombuManager, self).__init__(channel=channel,
                                           write_only=write_only,
                                           logger=logger)
        self.url = url
        self.producer = self._producer()

    def initialize(self):
        super(KombuManager, self).initialize()

        monkey_patched = True
        if self.server.async_mode == 'eventlet':
            from eventlet.patcher import is_monkey_patched
            monkey_patched = is_monkey_patched('socket')
        elif 'gevent' in self.server.async_mode:
            from gevent.monkey import is_module_patched
            monkey_patched = is_module_patched('socket')
        if not monkey_patched:
            raise RuntimeError(
                'Kombu requires a monkey patched socket library to work '
                'with ' + self.server.async_mode)

    def _connection(self):
        return kombu.Connection(self.url)

    def _exchange(self):
        return kombu.Exchange(self.channel, type='fanout', durable=False)

    def _queue(self):
        queue_name = 'flask-socketio.' + str(uuid.uuid4())
        return kombu.Queue(queue_name, self._exchange(),
                           durable=False,
                           queue_arguments={'x-expires': 300000})

    def _producer(self):
        return self._connection().Producer(exchange=self._exchange())

    def __error_callback(self, exception, interval):
        self._get_logger().exception('Sleeping {}s'.format(interval))

    def _publish(self, data):
        connection = self._connection()
        publish = connection.ensure(self.producer, self.producer.publish,
                                    errback=self.__error_callback)
        publish(pickle.dumps(data))

    def _listen(self):
        reader_queue = self._queue()

        while True:
            connection = self._connection().ensure_connection(
                errback=self.__error_callback)
            try:
                with connection.SimpleQueue(reader_queue) as queue:
                    while True:
                        message = queue.get(block=True)
                        message.ack()
                        yield message.payload
            except connection.connection_errors:
                self._get_logger().exception("Connection error "
                                             "while reading from queue")
