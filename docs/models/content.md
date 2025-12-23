# Content

Message content. Can be null when assistant message contains tool_calls.
- user/system messages: Required, contains text or multimodal content
- assistant messages: Optional when tool_calls is present; can be null or omitted
- tool messages: Required, contains tool return results (usually JSON string)

**Important:** In /v1/responses API, content field must exist and cannot be null.
For /v1/chat/completions, content can be null when tool_calls is present.



## Supported Types

### `str`

```python
value: str = /* values here */
```

### `List[models.MessageContent]`

```python
value: List[models.MessageContent] = /* values here */
```

