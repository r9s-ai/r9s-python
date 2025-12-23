# AnthropicToolResultContent


## Fields

| Field                                         | Type                                          | Required                                      | Description                                   |
| --------------------------------------------- | --------------------------------------------- | --------------------------------------------- | --------------------------------------------- |
| `type`                                        | *Literal["tool_result"]*                      | :heavy_check_mark:                            | N/A                                           |
| `tool_use_id`                                 | *str*                                         | :heavy_check_mark:                            | ID of the tool use this result corresponds to |
| `content`                                     | *str*                                         | :heavy_check_mark:                            | Result of the tool execution                  |