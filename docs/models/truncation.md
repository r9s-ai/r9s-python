# Truncation

The truncation strategy to use for the model response.
- auto: If input exceeds context window, truncate by dropping items from beginning
- disabled: Request fails with 400 error if input exceeds context window (default)



## Values

| Name       | Value      |
| ---------- | ---------- |
| `AUTO`     | auto       |
| `DISABLED` | disabled   |