from typing import TypeVar, Union, Awaitable

from taskchain.core.context import ExecutionContext
from taskchain.core.executable import Executable
from taskchain.core.outcome import Outcome
from taskchain.runtime.runner import AsyncRunner, SyncRunner

T = TypeVar("T")

def execute_flow(
    flow: Executable[T],
    data: T,
    async_mode: bool = False,
) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
    """
    Executes a flow, hiding the creation of context and runner.

    Args:
        flow: The flow or beat to execute.
        data: The input data object for the flow.
        async_mode: If True, uses AsyncRunner; otherwise, uses SyncRunner.

    Returns:
        The outcome of the flow execution.
    """
    ctx = ExecutionContext(data=data)
    if async_mode:
        runner = AsyncRunner()
        return runner.run(flow, ctx)
    else:
        runner = SyncRunner()
        return runner.run(flow, ctx)
