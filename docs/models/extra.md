# Extra

Engine-specific parameters. Different engines support different parameters:

**Exa engine parameters:**
- query (string, required): Search query
- num (integer): Number of results to return, default 10
- contents.text (boolean): Whether to return full text content

**Tavily engine parameters:**
- query (string, required): Search query
- max_results (integer): Maximum number of results, default 10
- search_depth (string): Search depth, "basic" or "advanced", default "basic"
- include_answer (boolean): Whether to include AI-generated summary answer, default true

**Google engine parameters:**
- query (string, required): Search query
- num (integer): Number of results (1-10), default 10
- start (integer): Starting position (pagination), default 1
- safe (string): Safe search, "active" or "off", default "active"



## Fields

| Field                                   | Type                                    | Required                                | Description                             |
| --------------------------------------- | --------------------------------------- | --------------------------------------- | --------------------------------------- |
| `query`                                 | *str*                                   | :heavy_check_mark:                      | Search query (required for all engines) |
| `__pydantic_extra__`                    | Dict[str, *Any*]                        | :heavy_minus_sign:                      | N/A                                     |