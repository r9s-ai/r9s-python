# ImageEditRequest

Request model for image editing (inpainting) operations.

## Fields

| Field             | Type                                                                       | Required           | Description                                                                |
| ----------------- | -------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------- |
| `image`           | [models.ImageFile](../models/imagefile.md)                                 | :heavy_check_mark: | The image(s) to edit. GPT image models accept up to 16 PNG, WebP, or JPG inputs under 50MB each; `dall-e-2` only accepts one square PNG under 4MB. |
| `prompt`          | *str*                                                                      | :heavy_check_mark: | A text description of the desired image(s). Max 32000 chars for GPT image models, 1000 for `dall-e-2`, and 4000 for `dall-e-3`. |
| `model`           | *Optional[str]*                                                            | :heavy_minus_sign: | The model to use for image editing.                                        |
| `mask`            | [Optional[models.ImageFile]](../models/imagefile.md)                       | :heavy_minus_sign: | Transparent edit mask. For GPT image models it must match the input image format and dimensions, include an alpha channel, and stay under 50MB; for `dall-e-2` it must be a PNG under 4MB with matching dimensions. |
| `n`               | *Optional[int]*                                                            | :heavy_minus_sign: | Number of images to generate. Range: 1-10. Default: 1                      |
| `size`            | [Optional[models.ImageEditSize]](../models/imageeditsize.md)               | :heavy_minus_sign: | Model-specific output size. GPT image models support `1024x1024`, `1536x1024`, `1024x1536`, or `auto`; `dall-e-2` supports `256x256`, `512x512`, or `1024x1024`; `dall-e-3` supports `1024x1024`, `1792x1024`, or `1024x1792`. |
| `response_format` | [Optional[models.ImageEditResponseFormat]](../models/imageeditresponseformat.md) | :heavy_minus_sign: | Output format for models that support it. `dall-e-2` and `dall-e-3` support `url` or `b64_json`; GPT image models always return base64 image data and do not support this parameter. |
| `user`            | *Optional[str]*                                                            | :heavy_minus_sign: | Unique identifier for end-user tracking.                                   |
