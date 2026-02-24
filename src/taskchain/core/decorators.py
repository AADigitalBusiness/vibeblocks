from typing import Callable, Optional, List, Type, Any, TypeVar, Union
from taskchain.components.task import Task
from taskchain.policies.retry import RetryPolicy, BackoffStrategy
from taskchain.core.context import ExecutionContext

T = TypeVar("T")

def task(
    name: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    undo: Optional[Callable[[ExecutionContext[Any]], Any]] = None,
    # Quick configuration arguments
    max_attempts: int = 1,
    delay: float = 1.0,
    backoff: BackoffStrategy = BackoffStrategy.FIXED,
    retry_on: Optional[List[Type[Exception]]] = None,
    give_up_on: Optional[List[Type[Exception]]] = None
) -> Callable[[Callable[[ExecutionContext[Any]], Any]], Task[Any]]:
    """
    Decorator to convert a function into a Task.
    """
    def decorator(func: Callable[[ExecutionContext[Any]], Any]) -> Task[Any]:
        nonlocal name, retry_policy
        task_name = name if name is not None else func.__name__

        policy = retry_policy
        if policy is None:
            policy = RetryPolicy(
                max_attempts=max_attempts,
                delay=delay,
                backoff=backoff,
                retry_on=retry_on or [Exception],
                give_up_on=give_up_on or []
            )

        return Task(
            name=task_name,
            func=func,
            retry_policy=policy,
            undo=undo
        )
    return decorator
