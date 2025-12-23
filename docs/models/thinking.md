# Thinking

Configuration for extended thinking (Claude 3.7+). When enabled, the model will spend more time thinking before responding.



## Fields

| Field                                                                                    | Type                                                                                     | Required                                                                                 | Description                                                                              |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `type`                                                                                   | [Optional[models.AnthropicMessageRequestType]](../models/anthropicmessagerequesttype.md) | :heavy_minus_sign:                                                                       | Whether to enable extended thinking                                                      |
| `budget_tokens`                                                                          | *Optional[int]*                                                                          | :heavy_minus_sign:                                                                       | Maximum number of tokens to use for thinking (1000-10000)                                |