# EmbeddingRequest


## Fields

| Field                                                              | Type                                                               | Required                                                           | Description                                                        |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `model`                                                            | *str*                                                              | :heavy_check_mark:                                                 | Model name                                                         |
| `input`                                                            | [models.EmbeddingRequestInput](../models/embeddingrequestinput.md) | :heavy_check_mark:                                                 | Input text                                                         |
| `encoding_format`                                                  | [Optional[models.EncodingFormat]](../models/encodingformat.md)     | :heavy_minus_sign:                                                 | N/A                                                                |
| `dimensions`                                                       | *Optional[int]*                                                    | :heavy_minus_sign:                                                 | Output dimensions                                                  |
| `user`                                                             | *Optional[str]*                                                    | :heavy_minus_sign:                                                 | N/A                                                                |