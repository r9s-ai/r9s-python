# Input

Input content, required parameter. Can be:
- String: Single text input
- Message array: Structured conversation history

**Important limitations:**
- Messages only support basic fields (role, content, name)
- Does not support tool_calls, tool_call_id and other tool-related fields
- content field is required and cannot be null
- To use tools, define them in the top-level tools parameter; model will call them on first response

Note: Responses API has deprecated messages parameter, now uses input parameter uniformly



## Supported Types

### `str`

```python
value: str = /* values here */
```

### `List[models.Message]`

```python
value: List[models.Message] = /* values here */
```

