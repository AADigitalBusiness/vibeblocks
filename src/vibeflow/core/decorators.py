"""
Decorators for wrapping user functions into library components.
"""

from functools import update_wrapper
from typing import Any, Callable, List, Optional, Type, TypeVar

from vibeflow.components.beat import Beat
from vibeflow.core.context import ExecutionContext
from vibeflow.policies.retry import BackoffStrategy, RetryPolicy

T = TypeVar("T")


def beat(
    name: Optional[str] = None,
    description: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    undo: Optional[Callable[[ExecutionContext[Any]], Any]] = None,
    timeout: Optional[float] = None,
    # Quick configuration arguments
    max_attempts: int = 1,
    delay: float = 1.0,
    backoff: BackoffStrategy = BackoffStrategy.FIXED,
    retry_on: Optional[List[Type[Exception]]] = None,
    give_up_on: Optional[List[Type[Exception]]] = None
) -> Callable[[Callable[[ExecutionContext[Any]], Any]], Beat[Any]]:
    """
    Decorator to convert a standard function into a `Beat` component.

    Parameters:
        name: Name of the beat (defaults to function name).
        description: Semantic description of the beat for AI/LLM contexts.
        retry_policy: Highly customizable policy object. Overrides quick config args when provided.
        undo: A callable that reverts changes made by the beat.

    Quick Retry Config Args (only used if `retry_policy` is NOT provided):
        max_attempts: Maximum total attempts before failing permanently (default: 1).
        delay: Base wait delay in seconds between retries (default: 1.0).
        backoff: Wait increment strategy (FIXED, LINEAR, or EXPONENTIAL) (default: FIXED).
        retry_on: List of Exception classes that trigger retries (default: [Exception]).
        give_up_on: List of Exception classes that explicitly skip retries (default: []).
    """
    def decorator(func: Callable[[ExecutionContext[Any]], Any]) -> Beat[Any]:
        nonlocal name, retry_policy
        beat_name = name if name is not None else func.__name__

        policy = retry_policy
        if policy is None:
            policy = RetryPolicy(
                max_attempts=max_attempts,
                delay=delay,
                backoff=backoff,
                retry_on=retry_on or [Exception],
                give_up_on=give_up_on or []
            )

        t = Beat(
            name=beat_name,
            func=func,
            description=description,
            retry_policy=policy,
            undo=undo,
            timeout=timeout
        )
        # Update wrapper to preserve metadata (docstrings, name, etc.)
        # We avoid updating __dict__ to prevent overwriting Beat internal attributes
        update_wrapper(t, func, updated=())
        return t
    return decorator
