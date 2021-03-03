from bot_arena_server.pubsub import PublishSubscribeService

import curio
import pytest


Pubsub = PublishSubscribeService

def async_run(f):
    return lambda *args, **kwargs: curio.run(f(*args, **kwargs))


@async_run
async def test_pubsub_works():
    ps = Pubsub()

    num_received = 0

    async def subscriber(delay, value):
        print('[Subscriber] start')
        await curio.sleep(delay)
        print('[Subscriber] delay done')
        assert await ps.receive() == value
        print('[Subscriber] got correct value')
        nonlocal num_received
        num_received += 1
        print('[Subscriber] set flag')

    async def publisher(delay, value):
        print('[Publisher] start')
        await curio.sleep(delay)
        print('[Publisher] delay done')
        await ps.publish(value)
        print('[Publisher] value published')

    num_received = 0
    tg = curio.TaskGroup(wait=all)
    await tg.spawn(subscriber, 0.0, 'foo')
    await tg.spawn(publisher, 0.1, 'foo')
    await tg.next_result()
    await tg.next_result()
    assert num_received == 1

    num_received = 0
    tg = curio.TaskGroup(wait=all)
    await tg.spawn(subscriber, 0.0, 'bar')
    await tg.spawn(subscriber, 0.0, 'bar')
    await tg.spawn(publisher, 0.1, 'bar')
    await tg.next_result()
    await tg.next_result()
    await tg.next_result()
    assert num_received == 2
