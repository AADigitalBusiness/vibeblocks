import inspect
from functools import partial
from typing import Any

def is_async_callable(obj: Any) -> bool:
    """
    Determines if an object is an async callable (coroutine function).
    Handles:
    - async def functions
    - functools.partial wrapping async functions
    - Callable objects with async def __call__
    """
    # Unwrap partials to inspect the underlying callable
    while isinstance(obj, partial):
        obj = obj.func

    # Check if the object itself is a coroutine function (covers async def)
    if inspect.iscoroutinefunction(obj):
        return True

    # Check if the object is a callable instance with an async __call__
    # Note: inspect.iscoroutinefunction(obj.__call__) works for methods too.
    if hasattr(obj, "__call__") and inspect.iscoroutinefunction(obj.__call__):
        return True

    return False
