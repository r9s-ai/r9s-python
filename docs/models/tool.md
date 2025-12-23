# Tool

Tool definition (nested format). Used for /v1/chat/completions and other endpoints.
Format: { "type": "function", "function": { "name": "...", "description": "...", "parameters": {...} } }



## Fields

| Field                                       | Type                                        | Required                                    | Description                                 |
| ------------------------------------------- | ------------------------------------------- | ------------------------------------------- | ------------------------------------------- |
| `type`                                      | [models.ToolType](../models/tooltype.md)    | :heavy_check_mark:                          | Tool type, currently only supports function |
| `function`                                  | [models.Function](../models/function.md)    | :heavy_check_mark:                          | N/A                                         |