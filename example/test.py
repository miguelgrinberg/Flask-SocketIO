import unittest
import app
from flask_socketio.test import event_packet, message_packet

class TestTestNamespace(unittest.TestCase):
    def test_on_my_event(self):
        s = app.socketio.test_client()
        s.emit('my event', namespace='/test', args=({'data':'test'},))
        self.assertTrue(len(s.packets), 1)
        self.assertEquals(s.packets[0], event_packet('my response', namespace='/test', args=({'data':'test'},)))
