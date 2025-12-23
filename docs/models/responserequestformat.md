# ResponseRequestFormat

An object specifying the format that the model must output. Setting to { "type": "json_schema", "name": "...", "schema": {...} } enables Structured Outputs which ensures the model will match your supplied JSON schema.
Setting to { "type": "json_object" } enables JSON mode, which ensures the model generates valid JSON.



## Fields

| Field                                                                    | Type                                                                     | Required                                                                 | Description                                                              |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| `type`                                                                   | [Optional[models.ResponseRequestType]](../models/responserequesttype.md) | :heavy_minus_sign:                                                       | The type of response format                                              |
| `name`                                                                   | *Optional[str]*                                                          | :heavy_minus_sign:                                                       | Name for the schema (required when type is json_schema)                  |
| `schema_`                                                                | Dict[str, *Any*]                                                         | :heavy_minus_sign:                                                       | JSON schema definition for structured outputs                            |
| `strict`                                                                 | *Optional[bool]*                                                         | :heavy_minus_sign:                                                       | Whether to enforce strict schema matching                                |