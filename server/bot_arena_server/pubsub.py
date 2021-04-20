import curio    # type: ignore

from typing import TypeVar, List, Generic


__all__ = [
    'PublishSubscribeService',
]


_T = TypeVar('_T')

class PublishSubscribeService(Generic[_T]):
    def __init__(self) -> None:
        self._queues: List[curio.Queue] = []

    async def publish(self, message: _T) -> None:
        # Safe handling of potential re-subscribers
        queues = self._queues
        self._queues = []

        for q in queues:
            await q.put(message)

            # Because it is impossible to create rendez-vouz queues in Curio (that is, with capacity 0),
            # we have to employ a workaround.
            await q.put(None)

    def subscribe(self) -> curio.Queue:
        q = curio.Queue(maxsize=1)
        self._queues.append(q)
        return q

    async def receive(self) -> _T:
        q = self.subscribe()
        return await q.get()
