from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from r9s.types import BaseModel


class GeminiInlineData(BaseModel):
    mime_type: str
    data: str


class GeminiFileData(BaseModel):
    mime_type: str
    file_uri: str


class GeminiContent(BaseModel):
    role: Optional[str] = None
    parts: List[Dict[str, Any]]


class GeminiGenerationConfig(BaseModel):
    temperature: Optional[float] = None
    top_p: Optional[float] = Field(default=None, alias="topP")
    top_k: Optional[int] = Field(default=None, alias="topK")
    candidate_count: Optional[int] = Field(default=None, alias="candidateCount")
    max_output_tokens: Optional[int] = Field(default=None, alias="maxOutputTokens")
    stop_sequences: Optional[List[str]] = Field(default=None, alias="stopSequences")
    response_mime_type: Optional[str] = Field(default=None, alias="responseMimeType")
    response_schema: Optional[Dict[str, Any]] = Field(
        default=None, alias="responseSchema"
    )
    response_json_schema: Optional[Dict[str, Any]] = Field(
        default=None, alias="responseJsonSchema"
    )
    internal_response_json_schema: Optional[Dict[str, Any]] = Field(
        default=None, alias="_responseJsonSchema"
    )
    seed: Optional[int] = None
    presence_penalty: Optional[float] = Field(default=None, alias="presencePenalty")
    frequency_penalty: Optional[float] = Field(
        default=None, alias="frequencyPenalty"
    )
    response_logprobs: Optional[bool] = Field(default=None, alias="responseLogprobs")
    logprobs: Optional[int] = None
    enable_enhanced_civic_answers: Optional[bool] = Field(
        default=None, alias="enableEnhancedCivicAnswers"
    )
    response_modalities: Optional[List[str]] = Field(
        default=None, alias="responseModalities"
    )
    speech_config: Optional[Dict[str, Any]] = Field(default=None, alias="speechConfig")
    thinking_config: Optional[Dict[str, Any]] = Field(
        default=None, alias="thinkingConfig"
    )
    image_config: Optional[Dict[str, Any]] = Field(default=None, alias="imageConfig")
    media_resolution: Optional[str] = Field(default=None, alias="mediaResolution")


class GeminiSafetySetting(BaseModel):
    category: str
    threshold: str


class GeminiSystemInstruction(BaseModel):
    parts: List[Dict[str, Any]]


class GeminiFunctionDeclaration(BaseModel):
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


class GeminiTool(BaseModel):
    function_declarations: Optional[List[GeminiFunctionDeclaration]] = Field(
        default=None, alias="functionDeclarations"
    )
    code_execution: Optional[Dict[str, Any]] = Field(
        default=None, alias="codeExecution"
    )


class GeminiToolConfig(BaseModel):
    function_calling_config: Optional[Dict[str, Any]] = Field(
        default=None, alias="functionCallingConfig"
    )


class GeminiGenerateContentRequest(BaseModel):
    contents: List[GeminiContent]
    generation_config: Optional[GeminiGenerationConfig] = Field(
        default=None, alias="generationConfig"
    )
    safety_settings: Optional[List[GeminiSafetySetting]] = Field(
        default=None, alias="safetySettings"
    )
    system_instruction: Optional[GeminiSystemInstruction] = Field(
        default=None, alias="systemInstruction"
    )
    tools: Optional[List[GeminiTool]] = None
    tool_config: Optional[GeminiToolConfig] = Field(default=None, alias="toolConfig")
    cached_content: Optional[str] = Field(default=None, alias="cachedContent")
    store: Optional[bool] = None


class GeminiSafetyRating(BaseModel):
    category: Optional[str] = None
    probability: Optional[str] = None
    blocked: Optional[bool] = None


class GeminiCandidate(BaseModel):
    content: Optional[GeminiContent] = None
    finish_reason: Optional[str] = Field(default=None, alias="finishReason")
    safety_ratings: Optional[List[GeminiSafetyRating]] = Field(
        default=None, alias="safetyRatings"
    )
    citation_metadata: Optional[Dict[str, Any]] = Field(
        default=None, alias="citationMetadata"
    )
    token_count: Optional[int] = Field(default=None, alias="tokenCount")
    grounding_attributions: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="groundingAttributions"
    )
    grounding_metadata: Optional[Dict[str, Any]] = Field(
        default=None, alias="groundingMetadata"
    )
    avg_logprobs: Optional[float] = Field(default=None, alias="avgLogprobs")
    logprobs_result: Optional[Dict[str, Any]] = Field(
        default=None, alias="logprobsResult"
    )
    url_context_metadata: Optional[Dict[str, Any]] = Field(
        default=None, alias="urlContextMetadata"
    )
    index: Optional[int] = None
    finish_message: Optional[str] = Field(default=None, alias="finishMessage")


class GeminiPromptFeedback(BaseModel):
    block_reason: Optional[str] = Field(default=None, alias="blockReason")
    safety_ratings: Optional[List[GeminiSafetyRating]] = Field(
        default=None, alias="safetyRatings"
    )


class GeminiUsageMetadata(BaseModel):
    prompt_token_count: Optional[int] = Field(default=None, alias="promptTokenCount")
    candidates_token_count: Optional[int] = Field(
        default=None, alias="candidatesTokenCount"
    )
    total_token_count: Optional[int] = Field(default=None, alias="totalTokenCount")
    cached_content_token_count: Optional[int] = Field(
        default=None, alias="cachedContentTokenCount"
    )


class GeminiGenerateContentResponse(BaseModel):
    candidates: Optional[List[GeminiCandidate]] = None
    prompt_feedback: Optional[GeminiPromptFeedback] = Field(
        default=None, alias="promptFeedback"
    )
    usage_metadata: Optional[GeminiUsageMetadata] = Field(
        default=None, alias="usageMetadata"
    )
    model_version: Optional[str] = Field(default=None, alias="modelVersion")
    response_id: Optional[str] = Field(default=None, alias="responseId")
    model_status: Optional[Dict[str, Any]] = Field(default=None, alias="modelStatus")


class GeminiSSEEnvelope(BaseModel):
    data: GeminiGenerateContentResponse
    id: Optional[str] = None
    event: Optional[str] = None
    retry: Optional[int] = None
