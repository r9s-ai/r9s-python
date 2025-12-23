# AnthropicMessageMessage


## Fields

| Field                                                                                | Type                                                                                 | Required                                                                             | Description                                                                          |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| `role`                                                                               | [models.AnthropicMessageMessageRole](../models/anthropicmessagemessagerole.md)       | :heavy_check_mark:                                                                   | Role of the message sender (user or assistant)                                       |
| `content`                                                                            | [models.AnthropicMessageMessageContent](../models/anthropicmessagemessagecontent.md) | :heavy_check_mark:                                                                   | Message content - can be array of content blocks or string                           |