from __future__ import absolute_import
import threading
import time

try:
    import queue
except ImportError:  # pragma: no cover
    import Queue as queue

_async = {
    'thread': threading.Thread,
    'queue': queue.Queue,
    'event': threading.Event,
    'websocket': None,
    'sleep': time.sleep,
}
