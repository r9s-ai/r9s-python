# ResponseUsage


## Fields

| Field                                                                    | Type                                                                     | Required                                                                 | Description                                                              |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| `input_tokens`                                                           | *int*                                                                    | :heavy_check_mark:                                                       | Number of tokens in the input                                            |
| `input_tokens_details`                                                   | [Optional[models.InputTokensDetails]](../models/inputtokensdetails.md)   | :heavy_minus_sign:                                                       | Details about input tokens                                               |
| `output_tokens`                                                          | *int*                                                                    | :heavy_check_mark:                                                       | Number of tokens in the output                                           |
| `output_tokens_details`                                                  | [Optional[models.OutputTokensDetails]](../models/outputtokensdetails.md) | :heavy_minus_sign:                                                       | Details about output tokens                                              |
| `total_tokens`                                                           | *int*                                                                    | :heavy_check_mark:                                                       | Total number of tokens (input + output)                                  |