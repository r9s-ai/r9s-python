# ImageEditRequest

Request model for image editing (inpainting) operations.

## Fields

| Field             | Type                                                                       | Required           | Description                                                                |
| ----------------- | -------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------- |
| `image`           | [models.ImageFile](../models/imagefile.md)                                 | :heavy_check_mark: | The image to edit. Must be PNG, less than 4MB, and square.                 |
| `prompt`          | *str*                                                                      | :heavy_check_mark: | A text description of the desired image(s).                                |
| `model`           | *Optional[str]*                                                            | :heavy_minus_sign: | The model to use for image editing.                                        |
| `mask`            | [Optional[models.ImageFile]](../models/imagefile.md)                       | :heavy_minus_sign: | PNG with transparent areas indicating where to edit.                       |
| `n`               | *Optional[int]*                                                            | :heavy_minus_sign: | Number of images to generate. Range: 1-10. Default: 1                      |
| `size`            | [Optional[models.ImageEditSize]](../models/imageeditsize.md)               | :heavy_minus_sign: | The size of the generated images. Default: "1024x1024"                     |
| `response_format` | [Optional[models.ImageEditResponseFormat]](../models/imageeditresponseformat.md) | :heavy_minus_sign: | Format of returned images: "url" (default) or "b64_json".                  |
| `user`            | *Optional[str]*                                                            | :heavy_minus_sign: | Unique identifier for end-user tracking.                                   |
