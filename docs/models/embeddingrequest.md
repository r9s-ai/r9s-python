# EmbeddingRequest


## Fields

| Field                                                              | Type                                                               | Required                                                           | Description                                                        |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `model`                                                            | *str*                                                              | :heavy_check_mark:                                                 | Embedding model identifier such as `text-embedding-3-small` or `text-embedding-3-large` |
| `input`                                                            | [models.EmbeddingRequestInput](../models/embeddingrequestinput.md) | :heavy_check_mark:                                                 | Input text or token arrays to embed. Each input is limited to 8192 tokens for current OpenAI embedding models, and the total tokens across all inputs must stay within the current OpenAI batch limit |
| `encoding_format`                                                  | [Optional[models.EncodingFormat]](../models/encodingformat.md)     | :heavy_minus_sign:                                                 | The format to return the embeddings in. Can be either `float` or `base64` |
| `dimensions`                                                       | *Optional[int]*                                                    | :heavy_minus_sign:                                                 | Output dimensions                                                  |
| `user`                                                             | *Optional[str]*                                                    | :heavy_minus_sign:                                                 | End-user identifier for abuse monitoring                           |
