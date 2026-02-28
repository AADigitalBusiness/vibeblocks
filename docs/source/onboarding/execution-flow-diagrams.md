# Execution Flow Diagrams

## Flow Success Path

```text
Start -> Beat 1 -> Beat 2 -> Beat 3 -> Success
```

## Flow Failure with Compensation

```text
Start -> Beat 1 -> Beat 2 -> Beat 3 fails
                  <- Undo Beat 2 <- Undo Beat 1
Result: Failed outcome after compensation
```

## Notes

- Compensation runs in reverse order of completed steps.
- Retry is applied per beat according to the configured policy.
