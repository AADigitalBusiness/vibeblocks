import inspect
from functools import partial
from typing import Any

def is_async_callable(obj: Any) -> bool:
    """
    Determines if an object is an async callable (coroutine function).
    
    Warning:
        This only detects functions strictly declared as `async def` or wrappers
        around them. If a regular `def` function manually returns a coroutine 
        (e.g., returning `asyncio.sleep()`), this function will return False, 
        and it could fail at execution time in synchronous environments.
        
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
    if callable(obj) and inspect.iscoroutinefunction(obj.__call__):
        return True

    return False
