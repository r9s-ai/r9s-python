# StopReason

Reason why the model stopped:
- end_turn: Natural completion
- max_tokens: Hit max_tokens limit
- stop_sequence: Hit a stop sequence
- tool_use: Model wants to use a tool
- pause_turn: Long-running task paused (extended thinking)
- refusal: Content policy violation



## Values

| Name            | Value           |
| --------------- | --------------- |
| `END_TURN`      | end_turn        |
| `MAX_TOKENS`    | max_tokens      |
| `STOP_SEQUENCE` | stop_sequence   |
| `TOOL_USE`      | tool_use        |
| `PAUSE_TURN`    | pause_turn      |
| `REFUSAL`       | refusal         |