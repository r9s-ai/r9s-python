# AudioSDK
(*audio*)

## Overview

### Available Operations

* [speech](#speech) - Text to speech
* [transcribe](#transcribe) - Speech to text
* [translate](#translate) - Speech translation

## speech

Convert text to speech

### Example Usage

<!-- UsageSnippet language="python" operationID="createAudioSpeech" method="post" path="/audio/speech" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.audio.speech(model="speech-2.6-turbo", input="Hello, welcome to our service!", voice="alloy", response_format="mp3", speed=1)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                             | Type                                                                                                  | Required                                                                                              | Description                                                                                           |
| ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `model`                                                                                               | *str*                                                                                                 | :heavy_check_mark:                                                                                    | TTS model name                                                                                        |
| `input`                                                                                               | *str*                                                                                                 | :heavy_check_mark:                                                                                    | Text to convert to speech                                                                             |
| `voice`                                                                                               | [models.AudioSpeechRequestVoice](../../models/audiospeechrequestvoice.md)                             | :heavy_check_mark:                                                                                    | Voice type                                                                                            |
| `response_format`                                                                                     | [Optional[models.AudioSpeechRequestResponseFormat]](../../models/audiospeechrequestresponseformat.md) | :heavy_minus_sign:                                                                                    | N/A                                                                                                   |
| `speed`                                                                                               | *Optional[float]*                                                                                     | :heavy_minus_sign:                                                                                    | Speech speed                                                                                          |
| `retries`                                                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                      | :heavy_minus_sign:                                                                                    | Configuration to override the default retry behavior of the client.                                   |

### Response

**[models.CreateAudioSpeechResponse](../../models/createaudiospeechresponse.md)**

### Errors

| Error Type                      | Status Code                     | Content Type                    |
| ------------------------------- | ------------------------------- | ------------------------------- |
| errors.BadRequestError          | 400                             | application/json                |
| errors.AuthenticationError      | 401                             | application/json                |
| errors.PermissionDeniedError    | 403                             | application/json                |
| errors.UnprocessableEntityError | 422                             | application/json                |
| errors.RateLimitError           | 429                             | application/json                |
| errors.InternalServerError      | 500                             | application/json                |
| errors.ServiceUnavailableError  | 503                             | application/json                |
| errors.R9SDefaultError          | 4XX, 5XX                        | \*/\*                           |

## transcribe

Transcribe speech to text. Supports multiple models and output formats.

**Supported models:**
- whisper-1: Supports json, text, srt, verbose_json, vtt formats
- gpt-4o-transcribe, gpt-4o-mini-transcribe: Only support json and text formats

**Note:** timestamp_granularities parameter only works when response_format is set to verbose_json


### Example Usage

<!-- UsageSnippet language="python" operationID="createAudioTranscription" method="post" path="/audio/transcriptions" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.audio.transcribe(file={
        "file_name": "example.file",
        "content": open("example.file", "rb"),
    }, model="whisper-1", response_format="json", temperature=0)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                                                      | Type                                                                                                                                                                                                                           | Required                                                                                                                                                                                                                       | Description                                                                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `file`                                                                                                                                                                                                                         | [models.File](../../models/file.md)                                                                                                                                                                                            | :heavy_check_mark:                                                                                                                                                                                                             | Audio file to transcribe                                                                                                                                                                                                       |
| `model`                                                                                                                                                                                                                        | *str*                                                                                                                                                                                                                          | :heavy_check_mark:                                                                                                                                                                                                             | Model name                                                                                                                                                                                                                     |
| `language`                                                                                                                                                                                                                     | *Optional[str]*                                                                                                                                                                                                                | :heavy_minus_sign:                                                                                                                                                                                                             | Audio language (ISO-639-1 format)                                                                                                                                                                                              |
| `prompt`                                                                                                                                                                                                                       | *Optional[str]*                                                                                                                                                                                                                | :heavy_minus_sign:                                                                                                                                                                                                             | Optional text prompt                                                                                                                                                                                                           |
| `response_format`                                                                                                                                                                                                              | [Optional[models.AudioTranscriptionRequestResponseFormat]](../../models/audiotranscriptionrequestresponseformat.md)                                                                                                            | :heavy_minus_sign:                                                                                                                                                                                                             | Output format. Model support varies:<br/>- whisper-1: Supports all formats (json, text, srt, verbose_json, vtt)<br/>- gpt-4o-transcribe, gpt-4o-mini-transcribe: Only json and text<br/>                                       |
| `temperature`                                                                                                                                                                                                                  | *Optional[float]*                                                                                                                                                                                                              | :heavy_minus_sign:                                                                                                                                                                                                             | N/A                                                                                                                                                                                                                            |
| `timestamp_granularities`                                                                                                                                                                                                      | List[[models.TimestampGranularities](../../models/timestampgranularities.md)]                                                                                                                                                  | :heavy_minus_sign:                                                                                                                                                                                                             | Timestamp granularity levels to include. Options: word, segment.<br/>**Important:** Only works when response_format is set to verbose_json.<br/>Note: segment timestamps have no additional latency, but word timestamps add latency.<br/> |
| `retries`                                                                                                                                                                                                                      | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                                               | :heavy_minus_sign:                                                                                                                                                                                                             | Configuration to override the default retry behavior of the client.                                                                                                                                                            |

### Response

**[models.CreateAudioTranscriptionResponse](../../models/createaudiotranscriptionresponse.md)**

### Errors

| Error Type                      | Status Code                     | Content Type                    |
| ------------------------------- | ------------------------------- | ------------------------------- |
| errors.BadRequestError          | 400                             | application/json                |
| errors.AuthenticationError      | 401                             | application/json                |
| errors.PermissionDeniedError    | 403                             | application/json                |
| errors.UnprocessableEntityError | 422                             | application/json                |
| errors.RateLimitError           | 429                             | application/json                |
| errors.InternalServerError      | 500                             | application/json                |
| errors.ServiceUnavailableError  | 503                             | application/json                |
| errors.R9SDefaultError          | 4XX, 5XX                        | \*/\*                           |

## translate

Translate speech from any supported language to English text.

**Important:** This endpoint only translates audio into English. The source language is automatically detected by the model.

**Supported models:** whisper-1 (primary), gpt-4o-transcribe (extended support)


### Example Usage

<!-- UsageSnippet language="python" operationID="createAudioTranslation" method="post" path="/audio/translations" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.audio.translate(file={
        "file_name": "example.file",
        "content": open("example.file", "rb"),
    }, model="whisper-1", response_format="json", temperature=0)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                             | Type                                                                                                                                                  | Required                                                                                                                                              | Description                                                                                                                                           |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `file`                                                                                                                                                | [models.AudioTranslationRequestFile](../../models/audiotranslationrequestfile.md)                                                                     | :heavy_check_mark:                                                                                                                                    | Audio file to translate to English                                                                                                                    |
| `model`                                                                                                                                               | *str*                                                                                                                                                 | :heavy_check_mark:                                                                                                                                    | Model name (whisper-1 is primary, gpt-4o-transcribe has extended support)                                                                             |
| `prompt`                                                                                                                                              | *Optional[str]*                                                                                                                                       | :heavy_minus_sign:                                                                                                                                    | Optional text prompt to guide the model's style.<br/>The source language can be specified in the prompt if needed, though the model will auto-detect it.<br/> |
| `response_format`                                                                                                                                     | [Optional[models.AudioTranslationRequestResponseFormat]](../../models/audiotranslationrequestresponseformat.md)                                       | :heavy_minus_sign:                                                                                                                                    | Output format for the translated text                                                                                                                 |
| `temperature`                                                                                                                                         | *Optional[float]*                                                                                                                                     | :heavy_minus_sign:                                                                                                                                    | Sampling temperature between 0 and 1                                                                                                                  |
| `retries`                                                                                                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                      | :heavy_minus_sign:                                                                                                                                    | Configuration to override the default retry behavior of the client.                                                                                   |

### Response

**[models.CreateAudioTranslationResponse](../../models/createaudiotranslationresponse.md)**

### Errors

| Error Type                      | Status Code                     | Content Type                    |
| ------------------------------- | ------------------------------- | ------------------------------- |
| errors.BadRequestError          | 400                             | application/json                |
| errors.AuthenticationError      | 401                             | application/json                |
| errors.PermissionDeniedError    | 403                             | application/json                |
| errors.UnprocessableEntityError | 422                             | application/json                |
| errors.RateLimitError           | 429                             | application/json                |
| errors.InternalServerError      | 500                             | application/json                |
| errors.ServiceUnavailableError  | 503                             | application/json                |
| errors.R9SDefaultError          | 4XX, 5XX                        | \*/\*                           |