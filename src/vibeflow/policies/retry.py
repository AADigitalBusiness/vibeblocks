"""
Retry logic and backoff strategies.
Provides classes to handle transient errors in tasks and workflows.
"""

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Sequence, Type


class BackoffStrategy(Enum):
    """
    Defines how the delay between retry intervals grows.
    """

    FIXED = auto()
    """Fixed delay across all attempts (delay = base_delay)."""

    LINEAR = auto()
    """
    Delays multiply linearly with the attempt's loop iteration.
    (delay = base_delay * attempt_num)
    """

    EXPONENTIAL = auto()
    """
    Delays multiply using base 2 to the power of the attempt num.
    (delay = base_delay * (2^(attempt_num-1)))
    """


@dataclass
class RetryPolicy:
    """Configuration for retry logic."""

    # Safety limits to prevent resource exhaustion
    MAX_ATTEMPTS_LIMIT = 100
    MAX_DELAY_LIMIT = 3600.0  # 1 hour

    max_attempts: int = 3
    delay: float = 1.0  # Base delay in seconds
    backoff: BackoffStrategy = BackoffStrategy.FIXED
    max_delay: float = 60.0
    jitter: bool = False
    retry_on: Sequence[Type[Exception]] = (Exception,)
    give_up_on: Sequence[Type[Exception]] = ()

    def __post_init__(self) -> None:
        """Validate and cap configuration values for safety."""
        # Ensure non-negative values
        if self.max_attempts < 0:
            self.max_attempts = 0
        if self.delay < 0:
            self.delay = 0.0
        if self.max_delay < 0:
            self.max_delay = 0.0

        # Cap at safety limits
        if self.max_attempts > self.MAX_ATTEMPTS_LIMIT:
            self.max_attempts = self.MAX_ATTEMPTS_LIMIT

        if self.max_delay > self.MAX_DELAY_LIMIT:
            self.max_delay = self.MAX_DELAY_LIMIT

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determines if a retry should occur based on attempts and exception type."""
        if attempt >= self.max_attempts:
            return False

        # Check give_up_on first
        if isinstance(exception, tuple(self.give_up_on)):
            return False

        # Check retry_on
        if isinstance(exception, tuple(self.retry_on)):
            return True

        return False

    def calculate_delay(self, attempt: int) -> float:
        """Calculates the delay before the next retry attempt."""
        # attempt is the number of the retry about to happen (1st retry, 2nd retry, etc.)
        if attempt < 1:
            return 0.0

        delay = self.delay
        if self.backoff == BackoffStrategy.LINEAR:
            delay = self.delay * attempt
        elif self.backoff == BackoffStrategy.EXPONENTIAL:
            delay = self.delay * (2 ** (attempt - 1))

        # Cap at max_delay
        if delay > self.max_delay:
            delay = self.max_delay

        if self.jitter:
            # Add random jitter between 0 and 10% of the delay
            delay += random.uniform(0, delay * 0.1)

        return delay
