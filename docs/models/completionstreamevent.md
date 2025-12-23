# CompletionStreamEvent

Completion stream event (data payload for SSE stream)


## Fields

| Field                                                                      | Type                                                                       | Required                                                                   | Description                                                                |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `id`                                                                       | *str*                                                                      | :heavy_check_mark:                                                         | N/A                                                                        |
| `object`                                                                   | *Literal["completion"]*                                                    | :heavy_check_mark:                                                         | N/A                                                                        |
| `created`                                                                  | *int*                                                                      | :heavy_check_mark:                                                         | Unix timestamp                                                             |
| `model`                                                                    | *str*                                                                      | :heavy_check_mark:                                                         | N/A                                                                        |
| `choices`                                                                  | List[[models.CompletionStreamChoice](../models/completionstreamchoice.md)] | :heavy_check_mark:                                                         | N/A                                                                        |
| `system_fingerprint`                                                       | *Optional[str]*                                                            | :heavy_minus_sign:                                                         | N/A                                                                        |
| `obfuscation`                                                              | *Optional[str]*                                                            | :heavy_minus_sign:                                                         | Obfuscation token (server-specific field)                                  |