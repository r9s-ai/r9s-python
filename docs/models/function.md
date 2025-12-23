# Function


## Fields

| Field                                                                   | Type                                                                    | Required                                                                | Description                                                             |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `name`                                                                  | *str*                                                                   | :heavy_check_mark:                                                      | Function name                                                           |
| `description`                                                           | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | Function description, helps model understand when to call this function |
| `parameters`                                                            | Dict[str, *Any*]                                                        | :heavy_minus_sign:                                                      | Function parameter definition in JSON Schema format                     |