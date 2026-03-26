# ImageEditSize

The size of the generated images for image editing operations.

## Values

| Value       | Description        |
| ----------- | ------------------ |
| `auto`      | Automatic size selection |
| `256x256`   | 256x256 pixels     |
| `512x512`   | 512x512 pixels     |
| `1024x1024` | 1024x1024 pixels   |
| `1024x1536` | 1024x1536 pixels   |
| `1536x1024` | 1536x1024 pixels   |
| `1024x1792` | 1024x1792 pixels   |
| `1792x1024` | 1792x1024 pixels   |

**Note:** Valid sizes depend on the model. GPT image models support `1024x1024`, `1024x1536`, `1536x1024`, or `auto`; `dall-e-2` supports `256x256`, `512x512`, or `1024x1024`; `dall-e-3` supports `1024x1024`, `1024x1792`, or `1792x1024`.
