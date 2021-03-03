from bot_arena_server.pubsub import PublishSubscribeService

import curio
import pytest


Pubsub = PublishSubscribeService

def async_run(f):
    return lambda *args, **kwargs: curio.run(f(*args, **kwargs))


@async_run
async def test_pubsub_works():
    ps = Pubsub()

    has_received = False

    async def subscriber(delay, value):
        await curio.sleep(delay)
        assert await ps.receive() == value

    async def publisher(delay, value):
        await curio.sleep(delay)
        await ps.publish(value)
        assert has_received

    has_received = False
    tg = curio.TaskGroup(wait=all)
    await tg.spawn(subscriber, 0.0, 'foo')
    await tg.spawn(publisher, 0.1, 'foo')
    await tg.next_result()
    await tg.next_result()

    has_received = False
    tg = curio.TaskGroup(wait=all)
    await tg.spawn(subscriber, 0.1, 'foo')
    await tg.spawn(publisher, 0.0, 'foo')
    await tg.next_result()
    await tg.next_result()
