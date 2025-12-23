# AudioTranscriptionResponse


## Fields

| Field                                          | Type                                           | Required                                       | Description                                    |
| ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| `text`                                         | *str*                                          | :heavy_check_mark:                             | Transcribed text                               |
| `language`                                     | *Optional[str]*                                | :heavy_minus_sign:                             | Detected language                              |
| `duration`                                     | *Optional[float]*                              | :heavy_minus_sign:                             | Audio duration (seconds)                       |
| `words`                                        | List[[models.Words](../models/words.md)]       | :heavy_minus_sign:                             | N/A                                            |
| `segments`                                     | List[[models.Segments](../models/segments.md)] | :heavy_minus_sign:                             | N/A                                            |