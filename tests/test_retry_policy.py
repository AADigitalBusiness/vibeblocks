from taskchain.policies.retry import RetryPolicy, BackoffStrategy

def test_should_retry_max_attempts():
    policy = RetryPolicy(max_attempts=3)
    assert policy.should_retry(0, Exception()) is True
    assert policy.should_retry(1, Exception()) is True
    assert policy.should_retry(2, Exception()) is True
    assert policy.should_retry(3, Exception()) is False
    assert policy.should_retry(4, Exception()) is False

def test_should_retry_give_up_on():
    policy = RetryPolicy(give_up_on=[ValueError])
    assert policy.should_retry(0, ValueError()) is False
    assert policy.should_retry(0, Exception()) is True

def test_should_retry_retry_on():
    policy = RetryPolicy(retry_on=[ValueError])
    assert policy.should_retry(0, ValueError()) is True
    assert policy.should_retry(0, KeyError()) is False

def test_should_retry_inheritance():
    # give_up_on with base class
    policy = RetryPolicy(give_up_on=[Exception])
    assert policy.should_retry(0, ValueError()) is False

    # retry_on with base class
    policy2 = RetryPolicy(retry_on=[Exception])
    assert policy2.should_retry(0, ValueError()) is True

def test_calculate_delay_fixed():
    policy = RetryPolicy(delay=2.0, backoff=BackoffStrategy.FIXED)
    assert policy.calculate_delay(1) == 2.0
    assert policy.calculate_delay(2) == 2.0
    assert policy.calculate_delay(3) == 2.0

def test_calculate_delay_linear():
    policy = RetryPolicy(delay=2.0, backoff=BackoffStrategy.LINEAR)
    assert policy.calculate_delay(1) == 2.0
    assert policy.calculate_delay(2) == 4.0
    assert policy.calculate_delay(3) == 6.0

def test_calculate_delay_exponential():
    policy = RetryPolicy(delay=2.0, backoff=BackoffStrategy.EXPONENTIAL)
    assert policy.calculate_delay(1) == 2.0  # 2.0 * (2^0)
    assert policy.calculate_delay(2) == 4.0  # 2.0 * (2^1)
    assert policy.calculate_delay(3) == 8.0  # 2.0 * (2^2)
    assert policy.calculate_delay(4) == 16.0 # 2.0 * (2^3)

def test_calculate_delay_max_delay():
    policy = RetryPolicy(delay=10.0, backoff=BackoffStrategy.LINEAR, max_delay=15.0)
    assert policy.calculate_delay(1) == 10.0
    assert policy.calculate_delay(2) == 15.0
    assert policy.calculate_delay(3) == 15.0

def test_calculate_delay_jitter():
    policy = RetryPolicy(delay=10.0, jitter=True)
    # With FIXED backoff (default), base delay is 10.0
    # Jitter adds 0 to 10% (0 to 1.0)
    for _ in range(100):
        delay = policy.calculate_delay(1)
        assert 10.0 <= delay <= 11.0

def test_calculate_delay_invalid_attempt():
    policy = RetryPolicy(delay=10.0)
    assert policy.calculate_delay(0) == 0.0
    assert policy.calculate_delay(-1) == 0.0
