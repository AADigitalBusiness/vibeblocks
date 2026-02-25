from taskchain.policies.retry import BackoffStrategy, RetryPolicy


def test_retry_policy_limits_defaults():
    """Test that default values are within limits."""
    policy = RetryPolicy()
    assert policy.max_attempts == 3
    assert policy.max_delay == 60.0

def test_retry_policy_caps_max_attempts():
    """Test that max_attempts is capped at MAX_ATTEMPTS_LIMIT."""
    policy = RetryPolicy(max_attempts=1000)
    assert policy.max_attempts == RetryPolicy.MAX_ATTEMPTS_LIMIT
    assert policy.max_attempts == 100

def test_retry_policy_caps_max_delay():
    """Test that max_delay is capped at MAX_DELAY_LIMIT."""
    policy = RetryPolicy(max_delay=10000.0)
    assert policy.max_delay == RetryPolicy.MAX_DELAY_LIMIT
    assert policy.max_delay == 3600.0

def test_retry_policy_caps_both():
    """Test that both values are capped simultaneously."""
    policy = RetryPolicy(max_attempts=1000, max_delay=10000.0)
    assert policy.max_attempts == 100
    assert policy.max_delay == 3600.0

def test_retry_policy_negative_values():
    """Test that negative values are capped at 0."""
    policy = RetryPolicy(max_attempts=-5, max_delay=-10.0, delay=-1.0)
    assert policy.max_attempts == 0
    assert policy.max_delay == 0.0
    assert policy.delay == 0.0

def test_retry_policy_boundary_values():
    """Test values exactly at the limits."""
    policy = RetryPolicy(max_attempts=100, max_delay=3600.0)
    assert policy.max_attempts == 100
    assert policy.max_delay == 3600.0

def test_retry_policy_just_below_limits():
    """Test values just below the limits."""
    policy = RetryPolicy(max_attempts=99, max_delay=3599.0)
    assert policy.max_attempts == 99
    assert policy.max_delay == 3599.0

def test_calculate_delay_with_limits():
    """Test that calculate_delay respects the capped max_delay."""
    # Exponential backoff would exceed 3600 quickly
    policy = RetryPolicy(
        max_attempts=100,
        delay=2.0,
        backoff=BackoffStrategy.EXPONENTIAL,
        max_delay=10000.0  # Should be capped to 3600.0
    )
    assert policy.max_delay == 3600.0

    # 2 * 2^11 = 4096 > 3600
    # attempt 12 -> 2^(12-1) = 2048. 2.0 * 2048 = 4096.
    delay = policy.calculate_delay(12)
    assert delay == 3600.0
