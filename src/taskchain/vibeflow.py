"""
VibeFlow dynamic orchestration layer.
Allows creating and executing flows from JSON descriptions on the fly.
"""

from typing import Any, Dict, List, Type, Optional, Union, Awaitable
from taskchain.components.flow import Flow
from taskchain.components.beat import Beat
from taskchain.policies.failure import FailureStrategy
from taskchain.utils.execution import execute_flow
from taskchain.core.outcome import Outcome

class VibeFlow:
    """
    Dynamic Orchestrator that builds and runs Flows from JSON definitions.
    """

    @staticmethod
    def run_from_json(
        json_request: Dict[str, Any],
        initial_data: Any,
        available_beats: Dict[str, Beat]
    ) -> Union[Outcome[Any], Awaitable[Outcome[Any]]]:
        """
        Parses a JSON request, constructs a Flow, and executes it.

        Args:
            json_request: A dictionary defining the flow.
                          Expected format:
                          {
                              "name": "MyDynamicFlow",
                              "steps": ["beat_1", "beat_2"],
                              "strategy": "ABORT" | "CONTINUE" | "COMPENSATE"
                          }
            initial_data: The data object to initialize ExecutionContext with.
            available_beats: A dictionary mapping step names (strings) to Beat instances.

        Returns:
            The outcome of the execution.
        """

        flow_name = json_request.get("name", "DynamicFlow")
        step_names = json_request.get("steps", [])
        strategy_str = json_request.get("strategy", "ABORT").upper()

        # Validate Strategy
        try:
            strategy = FailureStrategy[strategy_str]
        except KeyError:
            strategy = FailureStrategy.ABORT

        # Resolve Beats
        flow_steps = []
        for name in step_names:
            if name not in available_beats:
                raise ValueError(f"Beat '{name}' not found in available_beats.")
            flow_steps.append(available_beats[name])

        # Construct Flow
        flow = Flow(name=flow_name, steps=flow_steps, strategy=strategy)

        # Execute
        # We assume sync execution by default unless the flow is async,
        # but `execute_flow` helper handles context creation.
        # We need to detect if we should run async.
        # If any step is async, we should probably run async.
        is_async = flow.is_async

        return execute_flow(flow, initial_data, async_mode=is_async)
