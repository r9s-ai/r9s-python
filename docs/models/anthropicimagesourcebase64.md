# AnthropicImageSourceBase64


## Fields

| Field                                      | Type                                       | Required                                   | Description                                |
| ------------------------------------------ | ------------------------------------------ | ------------------------------------------ | ------------------------------------------ |
| `type`                                     | *Literal["base64"]*                        | :heavy_check_mark:                         | N/A                                        |
| `media_type`                               | [models.MediaType](../models/mediatype.md) | :heavy_check_mark:                         | MIME type of the image                     |
| `data`                                     | *str*                                      | :heavy_check_mark:                         | Base64-encoded image data                  |