"""
VibeBlocks dynamic orchestration layer.
Allows creating and executing flows from JSON descriptions on the fly.
"""

from typing import Any, Dict, List, Type, Optional, Union, Awaitable
from vibeblocks.components.flow import Flow
from vibeblocks.components.block import Block
from vibeblocks.policies.failure import FailureStrategy
from vibeblocks.utils.execution import execute_flow
from vibeblocks.core.outcome import Outcome


class VibeBlocks:
    """
    Dynamic Orchestrator that builds and runs Flows from JSON definitions.
    """

    @staticmethod
    def run_from_json(
        json_request: Dict[str, Any],
        initial_data: Any,
        available_blocks: Dict[str, Block]
    ) -> Union[Outcome[Any], Awaitable[Outcome[Any]]]:
        """
        Parses a JSON request, constructs a Flow, and executes it.

        Args:
            json_request: A dictionary defining the flow.
                          Expected format:
                          {
                              "name": "MyDynamicFlow",
                              "steps": ["block_1", "block_2"],
                              "strategy": "ABORT" | "CONTINUE" | "COMPENSATE"
                          }
            initial_data: The data object to initialize ExecutionContext with.
            available_blocks: A dictionary mapping step names (strings) to Block instances.

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

        # Resolve Blocks
        flow_steps = []
        for name in step_names:
            if name not in available_blocks:
                raise ValueError(
                    f"Block '{name}' not found in available_blocks.")
            flow_steps.append(available_blocks[name])

        # Construct Flow
        flow = Flow(name=flow_name, steps=flow_steps, strategy=strategy)

        # Execute
        # We assume sync execution by default unless the flow is async,
        # but `execute_flow` helper handles context creation.
        # We need to detect if we should run async.
        # If any step is async, we should probably run async.
        is_async = flow.is_async

        return execute_flow(flow, initial_data, async_mode=is_async)
