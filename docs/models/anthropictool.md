# AnthropicTool


## Fields

| Field                                                            | Type                                                             | Required                                                         | Description                                                      |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| `type`                                                           | *Optional[str]*                                                  | :heavy_minus_sign:                                               | Tool type for Anthropic built-in tools or tool runtimes.         |
| `name`                                                           | *Optional[str]*                                                  | :heavy_minus_sign:                                               | Tool name. Custom tools typically set this, and some built-in tools do as well. |
| `description`                                                    | *Optional[str]*                                                  | :heavy_minus_sign:                                               | N/A                                                              |
| `input_schema`                                                   | [Optional[models.AnthropicInputSchema]](../models/anthropicinputschema.md) | :heavy_minus_sign:                                               | Input schema for custom tools. Built-in tools may omit this.     |
