# ResponseFormat


## Fields

| Field                                                                  | Type                                                                   | Required                                                               | Description                                                            |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `type`                                                                 | [Optional[models.ResponseFormatType]](../models/responseformattype.md) | :heavy_minus_sign:                                                     | Output format type such as `text`, `json_object`, or `json_schema`     |
| `json_schema`                                                          | [Optional[models.JSONSchema]](../models/jsonschema.md)                 | :heavy_minus_sign:                                                     | JSON Schema definition used when `type` is `json_schema`               |
