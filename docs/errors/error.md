# Error


## Fields

| Field                   | Type                    | Required                | Description             |
| ----------------------- | ----------------------- | ----------------------- | ----------------------- |
| `message`               | *str*                   | :heavy_check_mark:      | Error message           |
| `type`                  | *str*                   | :heavy_check_mark:      | Error type              |
| `code`                  | *OptionalNullable[str]* | :heavy_minus_sign:      | Error code              |
| `param`                 | *Optional[str]*         | :heavy_minus_sign:      | Related parameter       |