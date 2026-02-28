from dataclasses import dataclass
from vibeblocks.components.block import Block
from vibeblocks.components.flow import Flow
from vibeblocks.core.context import ExecutionContext
from vibeblocks.policies.failure import FailureStrategy
from vibeblocks.policies.retry import RetryPolicy
from vibeblocks.runtime.runner import SyncRunner


@dataclass
class UserData:
    email: str
    user_id: str | None = None
    status: str = "pending"


def test_onboarding_success():
    data = UserData(email="test@example.com")
    ctx = ExecutionContext(data=data)

    def validate_email(ctx):
        if "@" not in ctx.data.email:
            raise ValueError("Invalid email")

    def create_account(ctx):
        ctx.data.user_id = "user_123"
        ctx.data.status = "created"

    def undo_create_account(ctx):
        ctx.data.user_id = None
        ctx.data.status = "deleted"

    def send_welcome_email(ctx):
        # Simulate success
        pass

    blocks = [
        Block("ValidateEmail", validate_email),
        Block("CreateAccount", create_account, undo=undo_create_account),
        Block("SendWelcomeEmail", send_welcome_email,
              retry_policy=RetryPolicy(max_attempts=3))
    ]

    flow = Flow("UserOnboarding", blocks, strategy=FailureStrategy.COMPENSATE)
    outcome = SyncRunner().run(flow, ctx)

    assert outcome.status == "SUCCESS"
    assert ctx.data.user_id == "user_123"
    assert ctx.data.status == "created"


def test_onboarding_failure_compensation():
    data = UserData(email="test@example.com")
    ctx = ExecutionContext(data=data)

    def validate_email(ctx): pass

    def create_account(ctx):
        ctx.data.user_id = "user_123"
        ctx.data.status = "created"

    def undo_create_account(ctx):
        ctx.data.user_id = None
        ctx.data.status = "deleted"

    def send_welcome_email(ctx):
        raise ConnectionError("Email service down")

    blocks = [
        Block("ValidateEmail", validate_email),
        Block("CreateAccount", create_account, undo=undo_create_account),
        Block("SendWelcomeEmail", send_welcome_email,
              retry_policy=RetryPolicy(max_attempts=2, delay=0.001))
    ]

    flow = Flow("UserOnboarding", blocks, strategy=FailureStrategy.COMPENSATE)
    outcome = SyncRunner().run(flow, ctx)

    assert outcome.status == "FAILED"
    # Account created then deleted
    assert ctx.data.status == "deleted"

    # Check trace for retries
    retries = [e for e in ctx.trace if "Retrying" in e.message]
    assert len(retries) >= 1
