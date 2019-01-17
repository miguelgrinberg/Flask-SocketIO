import itertools
import logging

import six

default_logger = logging.getLogger('socketio')


class BaseManager(object):
    """Manage client connections.

    This class keeps track of all the clients and the rooms they are in, to
    support the broadcasting of messages. The data used by this class is
    stored in a memory structure, making it appropriate only for single process
    services. More sophisticated storage backends can be implemented by
    subclasses.
    """
    def __init__(self):
        self.logger = None
        self.server = None
        self.rooms = {}
        self.callbacks = {}
        self.pending_disconnect = {}

    def set_server(self, server):
        self.server = server

    def initialize(self):
        """Invoked before the first request is received. Subclasses can add
        their initialization code here.
        """
        pass

    def get_namespaces(self):
        """Return an iterable with the active namespace names."""
        return six.iterkeys(self.rooms)

    def get_participants(self, namespace, room):
        """Return an iterable with the active participants in a room."""
        for sid, active in six.iteritems(self.rooms[namespace][room].copy()):
            yield sid

    def connect(self, sid, namespace):
        """Register a client connection to a namespace."""
        self.enter_room(sid, namespace, None)
        self.enter_room(sid, namespace, sid)

    def is_connected(self, sid, namespace):
        if namespace in self.pending_disconnect and \
                sid in self.pending_disconnect[namespace]:
            # the client is in the process of being disconnected
            return False
        try:
            return self.rooms[namespace][None][sid]
        except KeyError:
            pass

    def pre_disconnect(self, sid, namespace):
        """Put the client in the to-be-disconnected list.

        This allows the client data structures to be present while the
        disconnect handler is invoked, but still recognize the fact that the
        client is soon going away.
        """
        if namespace not in self.pending_disconnect:
            self.pending_disconnect[namespace] = []
        self.pending_disconnect[namespace].append(sid)

    def disconnect(self, sid, namespace):
        """Register a client disconnect from a namespace."""
        if namespace not in self.rooms:
            return
        rooms = []
        for room_name, room in six.iteritems(self.rooms[namespace].copy()):
            if sid in room:
                rooms.append(room_name)
        for room in rooms:
            self.leave_room(sid, namespace, room)
        if sid in self.callbacks and namespace in self.callbacks[sid]:
            del self.callbacks[sid][namespace]
            if len(self.callbacks[sid]) == 0:
                del self.callbacks[sid]
        if namespace in self.pending_disconnect and \
                sid in self.pending_disconnect[namespace]:
            self.pending_disconnect[namespace].remove(sid)
            if len(self.pending_disconnect[namespace]) == 0:
                del self.pending_disconnect[namespace]

    def enter_room(self, sid, namespace, room):
        """Add a client to a room."""
        if namespace not in self.rooms:
            self.rooms[namespace] = {}
        if room not in self.rooms[namespace]:
            self.rooms[namespace][room] = {}
        self.rooms[namespace][room][sid] = True

    def leave_room(self, sid, namespace, room):
        """Remove a client from a room."""
        try:
            del self.rooms[namespace][room][sid]
            if len(self.rooms[namespace][room]) == 0:
                del self.rooms[namespace][room]
                if len(self.rooms[namespace]) == 0:
                    del self.rooms[namespace]
        except KeyError:
            pass

    def close_room(self, room, namespace):
        """Remove all participants from a room."""
        try:
            for sid in self.get_participants(namespace, room):
                self.leave_room(sid, namespace, room)
        except KeyError:
            pass

    def get_rooms(self, sid, namespace):
        """Return the rooms a client is in."""
        r = []
        try:
            for room_name, room in six.iteritems(self.rooms[namespace]):
                if room_name is not None and sid in room and room[sid]:
                    r.append(room_name)
        except KeyError:
            pass
        return r

    def emit(self, event, data, namespace, room=None, skip_sid=None,
             callback=None, **kwargs):
        """Emit a message to a single client, a room, or all the clients
        connected to the namespace."""
        if namespace not in self.rooms or room not in self.rooms[namespace]:
            return
        for sid in self.get_participants(namespace, room):
            if sid != skip_sid:
                if callback is not None:
                    id = self._generate_ack_id(sid, namespace, callback)
                else:
                    id = None
                self.server._emit_internal(sid, event, data, namespace, id)

    def trigger_callback(self, sid, namespace, id, data):
        """Invoke an application callback."""
        callback = None
        try:
            callback = self.callbacks[sid][namespace][id]
        except KeyError:
            # if we get an unknown callback we just ignore it
            self._get_logger().warning('Unknown callback received, ignoring.')
        else:
            del self.callbacks[sid][namespace][id]
        if callback is not None:
            callback(*data)

    def _generate_ack_id(self, sid, namespace, callback):
        """Generate a unique identifier for an ACK packet."""
        namespace = namespace or '/'
        if sid not in self.callbacks:
            self.callbacks[sid] = {}
        if namespace not in self.callbacks[sid]:
            self.callbacks[sid][namespace] = {0: itertools.count(1)}
        id = six.next(self.callbacks[sid][namespace][0])
        self.callbacks[sid][namespace][id] = callback
        return id

    def _get_logger(self):
        """Get the appropriate logger

        Prevents uninitialized servers in write-only mode from failing.
        """

        if self.logger:
            return self.logger
        elif self.server:
            return self.server.logger
        else:
            return default_logger
