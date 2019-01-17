import asyncio

from .base_manager import BaseManager


class AsyncManager(BaseManager):
    """Manage a client list for an asyncio server."""
    async def emit(self, event, data, namespace, room=None, skip_sid=None,
                   callback=None, **kwargs):
        """Emit a message to a single client, a room, or all the clients
        connected to the namespace.

        Note: this method is a coroutine.
        """
        if namespace not in self.rooms or room not in self.rooms[namespace]:
            return
        tasks = []
        for sid in self.get_participants(namespace, room):
            if sid != skip_sid:
                if callback is not None:
                    id = self._generate_ack_id(sid, namespace, callback)
                else:
                    id = None
                tasks.append(self.server._emit_internal(sid, event, data,
                                                        namespace, id))
        if tasks == []:  # pragma: no cover
            return
        await asyncio.wait(tasks)

    async def close_room(self, room, namespace):
        """Remove all participants from a room.

        Note: this method is a coroutine.
        """
        return super().close_room(room, namespace)

    async def trigger_callback(self, sid, namespace, id, data):
        """Invoke an application callback.

        Note: this method is a coroutine.
        """
        callback = None
        try:
            callback = self.callbacks[sid][namespace][id]
        except KeyError:
            # if we get an unknown callback we just ignore it
            self._get_logger().warning('Unknown callback received, ignoring.')
        else:
            del self.callbacks[sid][namespace][id]
        if callback is not None:
            ret = callback(*data)
            if asyncio.iscoroutine(ret):
                try:
                    await ret
                except asyncio.CancelledError:  # pragma: no cover
                    pass
