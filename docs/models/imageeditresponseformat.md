# ImageEditResponseFormat

The format in which the generated images are returned for image editing operations.

## Values

| Value      | Description                                     |
| ---------- | ----------------------------------------------- |
| `url`      | Returns a URL to the generated image for models that support it |
| `b64_json` | Returns the image as base64-encoded JSON for models that support it |

**Note:** GPT image models do not support `response_format`; they always return base64 image data.
