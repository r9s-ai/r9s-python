# ModerationRequest


## Fields

| Field                                                                | Type                                                                 | Required                                                             | Description                                                          |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `input`                                                              | [models.ModerationRequestInput](../models/moderationrequestinput.md) | :heavy_check_mark:                                                   | Input to moderate. Can be plain text, an array of strings, or native moderation input items such as text/image objects |
| `model`                                                              | *Optional[str]*                                                      | :heavy_minus_sign:                                                   | Moderation model name. OpenAI currently documents `omni-moderation-latest` as the primary default |
