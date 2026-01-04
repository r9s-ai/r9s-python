# ImageFile

Image file for upload in image editing operations.

## Fields

| Field          | Type                                         | Required           | Description                                      |
| -------------- | -------------------------------------------- | ------------------ | ------------------------------------------------ |
| `file_name`    | *str*                                        | :heavy_check_mark: | The name of the file                             |
| `content`      | *Union[bytes, IO[bytes], io.BufferedReader]* | :heavy_check_mark: | The file content as bytes or a file-like object  |
| `content_type` | *Optional[str]*                              | :heavy_minus_sign: | The MIME type of the file (e.g., "image/png")    |
