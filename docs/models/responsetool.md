# ResponseTool

Tool definition (flat format). Dedicated for /v1/responses endpoint.
Format: { "type": "function", "name": "...", "description": "...", "parameters": {...} }



## Fields

| Field                                                                   | Type                                                                    | Required                                                                | Description                                                             |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `type`                                                                  | [models.ResponseToolType](../models/responsetooltype.md)                | :heavy_check_mark:                                                      | Tool type, currently only supports function                             |
| `name`                                                                  | *str*                                                                   | :heavy_check_mark:                                                      | Function name                                                           |
| `description`                                                           | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | Function description, helps model understand when to call this function |
| `parameters`                                                            | [Optional[models.Parameters]](../models/parameters.md)                  | :heavy_minus_sign:                                                      | Function parameter definition in JSON Schema format                     |