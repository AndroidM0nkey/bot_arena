from typing import Tuple, Any, Generic, TypeVar, Optional, Coroutine
from dataclasses import dataclass

from curio import TaskGroup, TaskCancelled  # type: ignore


_T = TypeVar('_T')

@dataclass
class Box(Generic[_T]):
    item: _T


async def select(**kwargs) -> Tuple[str, Any]:
    exception: Box[Optional[BaseException]] = Box(None)

    async with TaskGroup(wait=any) as tg:
        for tag, coro in kwargs.items():
            await tg.spawn(_wrap, tag, coro, exception)

    if exception.item is not None:
        raise exception.item

    return tg.result


async def _wrap(
    tag: str,
    coro: Coroutine[Any, Any, Any],
    exception: Box[Optional[BaseException]]
) -> Any:
    try:
        return (tag, await coro)
    except TaskCancelled:
        pass
    except BaseException as e:
        exception.item = e
