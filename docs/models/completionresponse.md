# CompletionResponse


## Fields

| Field                                                          | Type                                                           | Required                                                       | Description                                                    |
| -------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------- |
| `id`                                                           | *str*                                                          | :heavy_check_mark:                                             | N/A                                                            |
| `object`                                                       | *Literal["completion"]*                                        | :heavy_check_mark:                                             | N/A                                                            |
| `created`                                                      | *int*                                                          | :heavy_check_mark:                                             | N/A                                                            |
| `model`                                                        | *str*                                                          | :heavy_check_mark:                                             | N/A                                                            |
| `choices`                                                      | List[[models.CompletionChoice](../models/completionchoice.md)] | :heavy_check_mark:                                             | N/A                                                            |
| `usage`                                                        | [Optional[models.Usage]](../models/usage.md)                   | :heavy_minus_sign:                                             | N/A                                                            |