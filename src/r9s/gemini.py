from __future__ import annotations

from typing import Any, Mapping, NoReturn, Optional
from urllib.parse import quote

from r9s import errors, utils
from r9s._hooks import HookContext
from r9s.basesdk import BaseSDK
from r9s.models.gemini_models import (
    GeminiGenerateContentRequest,
    GeminiGenerateContentResponse,
    GeminiSSEEnvelope,
)
from r9s.types import OptionalNullable, UNSET
from r9s.utils import eventstreaming
from r9s.utils.unmarshal_json_response import unmarshal_json_response


class Gemini(BaseSDK):
    def _resolve_base_url(self, server_url: Optional[str]) -> str:
        base_url = server_url or self._get_url(None, None)
        return base_url[:-3] if base_url.endswith("/v1") else base_url

    def _normalize_model(self, model: str) -> str:
        return model.strip()

    def _extract_gemini_api_key(self) -> str:
        security = self.sdk_configuration.security
        if callable(security):
            security = security()

        api_key = getattr(security, "api_key", "") if security is not None else ""
        api_key = str(api_key).strip()
        if not api_key:
            raise ValueError("api_key is required for Gemini requests")
        if api_key.lower().startswith("bearer "):
            api_key = api_key[7:].strip()
        return api_key

    def _build_gemini_headers(
        self, http_headers: Optional[Mapping[str, str]]
    ) -> dict[str, str]:
        headers = dict(http_headers or {})
        headers["x-goog-api-key"] = self._extract_gemini_api_key()
        headers.pop("Authorization", None)
        return headers

    def _handle_error_response(self, http_res) -> NoReturn:
        response_data: Any = None
        if utils.match_response(http_res, "400", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.BadRequestErrorData, http_res, http_res_text
            )
            raise errors.BadRequestError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "401", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.AuthenticationErrorData, http_res, http_res_text
            )
            raise errors.AuthenticationError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "403", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.PermissionDeniedErrorData, http_res, http_res_text
            )
            raise errors.PermissionDeniedError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "422", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.UnprocessableEntityErrorData, http_res, http_res_text
            )
            raise errors.UnprocessableEntityError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "429", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.RateLimitErrorData, http_res, http_res_text
            )
            raise errors.RateLimitError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "500", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.InternalServerErrorData, http_res, http_res_text
            )
            raise errors.InternalServerError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "503", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.ServiceUnavailableErrorData, http_res, http_res_text
            )
            raise errors.ServiceUnavailableError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)

        http_res_text = utils.stream_to_text(http_res)
        raise errors.R9SDefaultError(
            "Unexpected response received", http_res, http_res_text
        )

    async def _handle_error_response_async(self, http_res) -> NoReturn:
        response_data: Any = None
        if utils.match_response(http_res, "400", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.BadRequestErrorData, http_res, http_res_text
            )
            raise errors.BadRequestError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "401", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.AuthenticationErrorData, http_res, http_res_text
            )
            raise errors.AuthenticationError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "403", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.PermissionDeniedErrorData, http_res, http_res_text
            )
            raise errors.PermissionDeniedError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "422", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.UnprocessableEntityErrorData, http_res, http_res_text
            )
            raise errors.UnprocessableEntityError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "429", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.RateLimitErrorData, http_res, http_res_text
            )
            raise errors.RateLimitError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "500", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.InternalServerErrorData, http_res, http_res_text
            )
            raise errors.InternalServerError(response_data, http_res, http_res_text)
        if utils.match_response(http_res, "503", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.ServiceUnavailableErrorData, http_res, http_res_text
            )
            raise errors.ServiceUnavailableError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)

        http_res_text = await utils.stream_to_text_async(http_res)
        raise errors.R9SDefaultError(
            "Unexpected response received", http_res, http_res_text
        )

    def generate_content(
        self,
        *,
        model: str,
        contents: list[Any],
        generation_config: Optional[Any] = None,
        safety_settings: Optional[list[Any]] = None,
        system_instruction: Optional[Any] = None,
        tools: Optional[list[Any]] = None,
        tool_config: Optional[Any] = None,
        cached_content: Optional[str] = None,
        store: Optional[bool] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> GeminiGenerateContentResponse:
        r"""Generate content (Gemini native API)

        Generate a non-streaming Gemini response.

        :param model: Gemini model name
        :param contents: Conversation history and multimodal input parts
        :param generation_config: Generation settings such as temperature, response MIME type, JSON schema, thinking, image, or speech config
        :param safety_settings: Per-category safety thresholds
        :param system_instruction: System instruction content
        :param tools: Tool declarations and built-in Gemini tools such as function calling or code execution
        :param tool_config: Tool invocation configuration
        :param cached_content: Cached content reference
        :param store: Overrides project-level logging behavior for the request
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = self._resolve_base_url(server_url)
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        request = GeminiGenerateContentRequest(
            contents=utils.get_pydantic_model(contents, list[Any]),
            generationConfig=utils.get_pydantic_model(generation_config, Optional[Any]),
            safetySettings=utils.get_pydantic_model(safety_settings, Optional[list[Any]]),
            systemInstruction=utils.get_pydantic_model(system_instruction, Optional[Any]),
            tools=utils.get_pydantic_model(tools, Optional[list[Any]]),
            toolConfig=utils.get_pydantic_model(tool_config, Optional[Any]),
            cachedContent=cached_content,
            store=store,
        )

        normalized_model = quote(self._normalize_model(model), safe="")
        req = self._build_request(
            method="POST",
            path=f"/v1beta/models/{normalized_model}:generateContent",
            base_url=base_url,
            url_variables=None,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=False,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=self._build_gemini_headers(http_headers),
            security=None,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", GeminiGenerateContentRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET and self.sdk_configuration.retry_config is not UNSET:
            retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url,
                operation_id="generateGeminiContent",
                oauth2_scopes=None,
                security_source=self.sdk_configuration.security,
            ),
            request=req,
            error_status_codes=["400", "401", "403", "422", "429", "4XX", "500", "503", "5XX"],
            stream=True,
            retry_config=retry_config,
        )

        if utils.match_response(http_res, "200", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            return unmarshal_json_response(
                GeminiGenerateContentResponse, http_res, http_res_text
            )

        return self._handle_error_response(http_res)

    def stream_generate_content(
        self,
        *,
        model: str,
        contents: list[Any],
        generation_config: Optional[Any] = None,
        safety_settings: Optional[list[Any]] = None,
        system_instruction: Optional[Any] = None,
        tools: Optional[list[Any]] = None,
        tool_config: Optional[Any] = None,
        cached_content: Optional[str] = None,
        store: Optional[bool] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> eventstreaming.EventStream[GeminiGenerateContentResponse]:
        r"""Generate content stream (Gemini native API)

        Generate a streaming Gemini response over Server-Sent Events.

        :param model: Gemini model name
        :param contents: Conversation history and multimodal input parts
        :param generation_config: Generation settings such as temperature, response MIME type, JSON schema, thinking, image, or speech config
        :param safety_settings: Per-category safety thresholds
        :param system_instruction: System instruction content
        :param tools: Tool declarations and built-in Gemini tools such as function calling or code execution
        :param tool_config: Tool invocation configuration
        :param cached_content: Cached content reference
        :param store: Overrides project-level logging behavior for the request
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = self._resolve_base_url(server_url)
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        request = GeminiGenerateContentRequest(
            contents=utils.get_pydantic_model(contents, list[Any]),
            generationConfig=utils.get_pydantic_model(generation_config, Optional[Any]),
            safetySettings=utils.get_pydantic_model(safety_settings, Optional[list[Any]]),
            systemInstruction=utils.get_pydantic_model(system_instruction, Optional[Any]),
            tools=utils.get_pydantic_model(tools, Optional[list[Any]]),
            toolConfig=utils.get_pydantic_model(tool_config, Optional[Any]),
            cachedContent=cached_content,
            store=store,
        )

        normalized_model = quote(self._normalize_model(model), safe="")
        url_override = (
            f"{base_url}/v1beta/models/{normalized_model}:streamGenerateContent?alt=sse"
        )
        req = self._build_request(
            method="POST",
            path=f"/v1beta/models/{normalized_model}:streamGenerateContent",
            base_url=base_url,
            url_variables=None,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=False,
            user_agent_header="user-agent",
            accept_header_value="text/event-stream",
            http_headers=self._build_gemini_headers(http_headers),
            security=None,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", GeminiGenerateContentRequest
            ),
            allow_empty_value=None,
            url_override=url_override,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET and self.sdk_configuration.retry_config is not UNSET:
            retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url,
                operation_id="streamGeminiContent",
                oauth2_scopes=None,
                security_source=self.sdk_configuration.security,
            ),
            request=req,
            error_status_codes=["400", "401", "403", "422", "429", "4XX", "500", "503", "5XX"],
            stream=True,
            retry_config=retry_config,
        )

        if utils.match_response(http_res, "200", "text/event-stream"):
            return eventstreaming.EventStream(
                http_res,
                lambda raw: utils.unmarshal_json(raw, GeminiSSEEnvelope).data,
                client_ref=self,
            )

        if utils.match_response(http_res, "200", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.R9SDefaultError(
                "Expected Gemini SSE response",
                http_res,
                http_res_text,
            )

        return self._handle_error_response(http_res)

    async def generate_content_async(
        self,
        *,
        model: str,
        contents: list[Any],
        generation_config: Optional[Any] = None,
        safety_settings: Optional[list[Any]] = None,
        system_instruction: Optional[Any] = None,
        tools: Optional[list[Any]] = None,
        tool_config: Optional[Any] = None,
        cached_content: Optional[str] = None,
        store: Optional[bool] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> GeminiGenerateContentResponse:
        r"""Generate content (Gemini native API)

        Generate a non-streaming Gemini response asynchronously.

        :param model: Gemini model name
        :param contents: Conversation history and multimodal input parts
        :param generation_config: Generation settings such as temperature, response MIME type, JSON schema, thinking, image, or speech config
        :param safety_settings: Per-category safety thresholds
        :param system_instruction: System instruction content
        :param tools: Tool declarations and built-in Gemini tools such as function calling or code execution
        :param tool_config: Tool invocation configuration
        :param cached_content: Cached content reference
        :param store: Overrides project-level logging behavior for the request
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = self._resolve_base_url(server_url)
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        request = GeminiGenerateContentRequest(
            contents=utils.get_pydantic_model(contents, list[Any]),
            generationConfig=utils.get_pydantic_model(generation_config, Optional[Any]),
            safetySettings=utils.get_pydantic_model(safety_settings, Optional[list[Any]]),
            systemInstruction=utils.get_pydantic_model(system_instruction, Optional[Any]),
            tools=utils.get_pydantic_model(tools, Optional[list[Any]]),
            toolConfig=utils.get_pydantic_model(tool_config, Optional[Any]),
            cachedContent=cached_content,
            store=store,
        )

        normalized_model = quote(self._normalize_model(model), safe="")
        req = self._build_request_async(
            method="POST",
            path=f"/v1beta/models/{normalized_model}:generateContent",
            base_url=base_url,
            url_variables=None,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=False,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=self._build_gemini_headers(http_headers),
            security=None,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", GeminiGenerateContentRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET and self.sdk_configuration.retry_config is not UNSET:
            retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url,
                operation_id="generateGeminiContentAsync",
                oauth2_scopes=None,
                security_source=self.sdk_configuration.security,
            ),
            request=req,
            error_status_codes=["400", "401", "403", "422", "429", "4XX", "500", "503", "5XX"],
            stream=True,
            retry_config=retry_config,
        )

        if utils.match_response(http_res, "200", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            return unmarshal_json_response(
                GeminiGenerateContentResponse, http_res, http_res_text
            )

        return await self._handle_error_response_async(http_res)

    async def stream_generate_content_async(
        self,
        *,
        model: str,
        contents: list[Any],
        generation_config: Optional[Any] = None,
        safety_settings: Optional[list[Any]] = None,
        system_instruction: Optional[Any] = None,
        tools: Optional[list[Any]] = None,
        tool_config: Optional[Any] = None,
        cached_content: Optional[str] = None,
        store: Optional[bool] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> eventstreaming.EventStreamAsync[GeminiGenerateContentResponse]:
        r"""Generate content stream (Gemini native API)

        Generate a streaming Gemini response asynchronously over Server-Sent Events.

        :param model: Gemini model name
        :param contents: Conversation history and multimodal input parts
        :param generation_config: Generation settings such as temperature, response MIME type, JSON schema, thinking, image, or speech config
        :param safety_settings: Per-category safety thresholds
        :param system_instruction: System instruction content
        :param tools: Tool declarations and built-in Gemini tools such as function calling or code execution
        :param tool_config: Tool invocation configuration
        :param cached_content: Cached content reference
        :param store: Overrides project-level logging behavior for the request
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = self._resolve_base_url(server_url)
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        request = GeminiGenerateContentRequest(
            contents=utils.get_pydantic_model(contents, list[Any]),
            generationConfig=utils.get_pydantic_model(generation_config, Optional[Any]),
            safetySettings=utils.get_pydantic_model(safety_settings, Optional[list[Any]]),
            systemInstruction=utils.get_pydantic_model(system_instruction, Optional[Any]),
            tools=utils.get_pydantic_model(tools, Optional[list[Any]]),
            toolConfig=utils.get_pydantic_model(tool_config, Optional[Any]),
            cachedContent=cached_content,
            store=store,
        )

        normalized_model = quote(self._normalize_model(model), safe="")
        url_override = (
            f"{base_url}/v1beta/models/{normalized_model}:streamGenerateContent?alt=sse"
        )
        req = self._build_request_async(
            method="POST",
            path=f"/v1beta/models/{normalized_model}:streamGenerateContent",
            base_url=base_url,
            url_variables=None,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=False,
            user_agent_header="user-agent",
            accept_header_value="text/event-stream",
            http_headers=self._build_gemini_headers(http_headers),
            security=None,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", GeminiGenerateContentRequest
            ),
            allow_empty_value=None,
            url_override=url_override,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET and self.sdk_configuration.retry_config is not UNSET:
            retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url,
                operation_id="streamGeminiContentAsync",
                oauth2_scopes=None,
                security_source=self.sdk_configuration.security,
            ),
            request=req,
            error_status_codes=["400", "401", "403", "422", "429", "4XX", "500", "503", "5XX"],
            stream=True,
            retry_config=retry_config,
        )

        if utils.match_response(http_res, "200", "text/event-stream"):
            return eventstreaming.EventStreamAsync(
                http_res,
                lambda raw: utils.unmarshal_json(raw, GeminiSSEEnvelope).data,
                client_ref=self,
            )

        if utils.match_response(http_res, "200", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.R9SDefaultError(
                "Expected Gemini SSE response",
                http_res,
                http_res_text,
            )

        return await self._handle_error_response_async(http_res)
