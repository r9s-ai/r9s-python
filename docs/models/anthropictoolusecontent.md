# AnthropicToolUseContent


## Fields

| Field                               | Type                                | Required                            | Description                         |
| ----------------------------------- | ----------------------------------- | ----------------------------------- | ----------------------------------- |
| `type`                              | *Literal["tool_use"]*               | :heavy_check_mark:                  | N/A                                 |
| `id`                                | *str*                               | :heavy_check_mark:                  | Unique identifier for this tool use |
| `name`                              | *str*                               | :heavy_check_mark:                  | Name of the tool being called       |
| `input`                             | Dict[str, *Any*]                    | :heavy_check_mark:                  | Input parameters for the tool       |