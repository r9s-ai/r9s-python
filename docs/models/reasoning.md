# Reasoning

Configuration for reasoning models (e.g., o1, o3, gpt-5). Controls how the model uses reasoning tokens to "think" through the problem.


## Fields

| Field                                                                                        | Type                                                                                         | Required                                                                                     | Description                                                                                  |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `effort`                                                                                     | [Optional[models.Effort]](../models/effort.md)                                               | :heavy_minus_sign:                                                                           | The effort level for reasoning (none/minimal=fast, low/medium=balanced, high/xhigh=thorough) |
| `summary`                                                                                    | *Optional[str]*                                                                              | :heavy_minus_sign:                                                                           | Summary of reasoning approach                                                                |