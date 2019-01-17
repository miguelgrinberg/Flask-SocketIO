import importlib
import time

try:
    queue = importlib.import_module('queue')
except ImportError:  # pragma: no cover
    queue = importlib.import_module('Queue')  # pragma: no cover

_async = {
    'threading': importlib.import_module('threading'),
    'thread_class': 'Thread',
    'queue': queue,
    'queue_class': 'Queue',
    'websocket': None,
    'websocket_class': None,
    'sleep': time.sleep
}
