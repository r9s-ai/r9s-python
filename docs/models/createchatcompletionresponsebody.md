# CreateChatCompletionResponseBody

Successful response


## Fields

| Field                                                                      | Type                                                                       | Required                                                                   | Description                                                                |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `data`                                                                     | [models.ChatCompletionStreamEvent](../models/chatcompletionstreamevent.md) | :heavy_check_mark:                                                         | Chat completion chunk event (data payload for SSE stream)                  |
| `id`                                                                       | *Optional[str]*                                                            | :heavy_minus_sign:                                                         | N/A                                                                        |
| `event`                                                                    | *Optional[str]*                                                            | :heavy_minus_sign:                                                         | N/A                                                                        |
| `retry`                                                                    | *Optional[int]*                                                            | :heavy_minus_sign:                                                         | N/A                                                                        |