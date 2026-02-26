# Execution Flow Diagrams

## Workflow Success Path

```text
Start -> Task 1 -> Task 2 -> Task 3 -> Success
```

## Workflow Failure with Compensation

```text
Start -> Task 1 -> Task 2 -> Task 3 fails
                  <- Undo Task 2 <- Undo Task 1
Result: Failed outcome after compensation
```

## Notes

- Compensation runs in reverse order of completed steps.
- Retry is applied per task according to the configured policy.
