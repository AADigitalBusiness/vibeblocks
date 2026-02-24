from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Type, List
import random

class BackoffStrategy(Enum):
    FIXED = auto()
    LINEAR = auto()
    EXPONENTIAL = auto()

@dataclass
class RetryPolicy:
    """Configuration for retry logic."""
    max_attempts: int = 3
    delay: float = 1.0  # Base delay in seconds
    backoff: BackoffStrategy = BackoffStrategy.FIXED
    max_delay: float = 60.0
    jitter: bool = False
    retry_on: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    give_up_on: List[Type[Exception]] = field(default_factory=list)

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determines if a retry should occur based on attempts and exception type."""
        if attempt >= self.max_attempts:
            return False

        # Check give_up_on first
        for exc_type in self.give_up_on:
            if isinstance(exception, exc_type):
                return False

        # Check retry_on
        for exc_type in self.retry_on:
            if isinstance(exception, exc_type):
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
