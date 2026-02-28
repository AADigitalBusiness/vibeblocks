# Execution Flow Diagrams

## Flow Success Path

```text
Start -> Block 1 -> Block 2 -> Block 3 -> Success
```

## Flow Failure with Compensation

```text
Start -> Block 1 -> Block 2 -> Block 3 fails
                  <- Undo Block 2 <- Undo Block 1
Result: Failed outcome after compensation
```

## Notes

- Compensation runs in reverse order of completed steps.
- Retry is applied per block according to the configured policy.
