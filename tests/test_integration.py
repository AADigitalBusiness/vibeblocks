from dataclasses import dataclass
from taskchain.components.task import Task
from taskchain.components.workflow import Workflow
from taskchain.core.context import ExecutionContext
from taskchain.policies.failure import FailureStrategy
from taskchain.policies.retry import RetryPolicy
from taskchain.runtime.runner import SyncRunner

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

    tasks = [
        Task("ValidateEmail", validate_email),
        Task("CreateAccount", create_account, undo=undo_create_account),
        Task("SendWelcomeEmail", send_welcome_email, retry_policy=RetryPolicy(max_attempts=3))
    ]

    workflow = Workflow("UserOnboarding", tasks, strategy=FailureStrategy.COMPENSATE)
    outcome = SyncRunner().run(workflow, ctx)

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

    tasks = [
        Task("ValidateEmail", validate_email),
        Task("CreateAccount", create_account, undo=undo_create_account),
        Task("SendWelcomeEmail", send_welcome_email, retry_policy=RetryPolicy(max_attempts=2, delay=0.001))
    ]

    workflow = Workflow("UserOnboarding", tasks, strategy=FailureStrategy.COMPENSATE)
    outcome = SyncRunner().run(workflow, ctx)

    assert outcome.status == "FAILED"
    # Account created then deleted
    assert ctx.data.status == "deleted"

    # Check trace for retries
    retries = [e for e in ctx.trace if "Retrying" in e.message]
    assert len(retries) >= 1
