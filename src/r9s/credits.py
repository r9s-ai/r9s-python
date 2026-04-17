from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Mapping, Optional

from r9s import errors, utils
from r9s._hooks import HookContext
from r9s.basesdk import BaseSDK
from r9s.models.credits_models import CreditsUsageResponse, GetCreditsUsageRequest
from r9s.types import OptionalNullable, UNSET
from r9s.utils.unmarshal_json_response import unmarshal_json_response

_DEFAULT_MANAGE_BASE_URL = "https://portal-api.r9s.ai/api/v1"


class Credits(BaseSDK):
    def _resolve_base_url(self, server_url: Optional[str]) -> str:
        if server_url:
            return server_url.rstrip("/")
        return _DEFAULT_MANAGE_BASE_URL

    def _extract_manage_key(self, manage_key: Optional[str] = None) -> str:
        if manage_key is None:
            manage_key = self.sdk_configuration.manage_key
        manage_key = str(manage_key or "").strip()
        if not manage_key:
            raise ValueError("manage_key is required for credits requests")
        return manage_key

    def _build_headers(
        self,
        http_headers: Optional[Mapping[str, str]],
        manage_key: Optional[str] = None,
    ) -> dict[str, str]:
        headers = dict(http_headers or {})
        headers["Authorization"] = f"Bearer {self._extract_manage_key(manage_key)}"
        return headers

    def _coerce_timestamp(
        self, value: int | float | str | datetime | date, field_name: str
    ) -> int:
        if isinstance(value, bool):
            raise TypeError(f"{field_name} must be a timestamp or time string")

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        local_tz = datetime.now().astimezone().tzinfo

        if isinstance(value, datetime):
            dt = value
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=local_tz)
            return int(dt.timestamp())

        if isinstance(value, date):
            dt = datetime.combine(value, time.min)
            return int(dt.replace(tzinfo=local_tz).timestamp())

        raw = value.strip()
        if not raw:
            raise ValueError(f"{field_name} cannot be empty")

        if raw.isdigit():
            return int(raw)

        try:
            dt = utils.parse_datetime(raw)
        except ValueError:
            try:
                parsed_date = date.fromisoformat(raw)
            except ValueError as exc:
                raise ValueError(
                    f"{field_name} must be a Unix timestamp or ISO 8601/date string"
                ) from exc
            dt = datetime.combine(parsed_date, time.min)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=local_tz)

        return int(dt.timestamp())

    def _default_range(self) -> tuple[int, int]:
        local_now = datetime.now().astimezone()
        start_of_today = datetime.combine(
            local_now.date(), time.min, tzinfo=local_now.tzinfo
        )
        start_time = start_of_today - timedelta(days=3)
        end_time = start_of_today + timedelta(days=4)
        return int(start_time.timestamp()), int(end_time.timestamp())

    def _normalize_range(
        self,
        start_time: int | float | str | datetime | date | None,
        end_time: int | float | str | datetime | date | None,
    ) -> tuple[int, int]:
        if start_time is None and end_time is None:
            normalized = self._default_range()
        elif start_time is None or end_time is None:
            raise ValueError(
                "start_time and end_time must both be provided, or both omitted"
            )
        else:
            normalized = (
                self._coerce_timestamp(start_time, "start_time"),
                self._coerce_timestamp(end_time, "end_time"),
            )

        if normalized[0] > normalized[1]:
            raise ValueError("start_time must be less than or equal to end_time")

        return normalized

    def _handle_error_response(self, http_res) -> Any:
        response_data: Any = None
        if utils.match_response(http_res, "400", "application/json"):
            response_data = unmarshal_json_response(errors.BadRequestErrorData, http_res)
            raise errors.BadRequestError(response_data, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.CreditsAuthenticationErrorData, http_res
            )
            raise errors.AuthenticationError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.PermissionDeniedErrorData, http_res
            )
            raise errors.PermissionDeniedError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.InternalServerErrorData, http_res
            )
            raise errors.InternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)

        raise errors.R9SDefaultError("Unexpected response received", http_res)

    async def _handle_error_response_async(self, http_res) -> Any:
        response_data: Any = None
        if utils.match_response(http_res, "400", "application/json"):
            response_data = unmarshal_json_response(errors.BadRequestErrorData, http_res)
            raise errors.BadRequestError(response_data, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.CreditsAuthenticationErrorData, http_res
            )
            raise errors.AuthenticationError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.PermissionDeniedErrorData, http_res
            )
            raise errors.PermissionDeniedError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.InternalServerErrorData, http_res
            )
            raise errors.InternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.R9SDefaultError("API error occurred", http_res, http_res_text)

        raise errors.R9SDefaultError("Unexpected response received", http_res)

    def usage(
        self,
        *,
        start_time: int | float | str | datetime | date | None = None,
        end_time: int | float | str | datetime | date | None = None,
        manage_key: Optional[str] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> CreditsUsageResponse:
        base_url = self._resolve_base_url(server_url)
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        normalized_start, normalized_end = self._normalize_range(start_time, end_time)
        request = GetCreditsUsageRequest(
            start_time=normalized_start,
            end_time=normalized_end,
        )

        req = self._build_request(
            method="GET",
            path="/portal/management/usage",
            base_url=base_url,
            url_variables=None,
            request=request,
            request_body_required=False,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=self._build_headers(http_headers, manage_key),
            security=None,
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
                operation_id="getCreditsUsage",
                oauth2_scopes=None,
                security_source=None,
            ),
            request=req,
            error_status_codes=["400", "401", "403", "4XX", "500", "5XX"],
            retry_config=retry_config,
        )

        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(CreditsUsageResponse, http_res)

        return self._handle_error_response(http_res)

    async def usage_async(
        self,
        *,
        start_time: int | float | str | datetime | date | None = None,
        end_time: int | float | str | datetime | date | None = None,
        manage_key: Optional[str] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> CreditsUsageResponse:
        base_url = self._resolve_base_url(server_url)
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        normalized_start, normalized_end = self._normalize_range(start_time, end_time)
        request = GetCreditsUsageRequest(
            start_time=normalized_start,
            end_time=normalized_end,
        )

        req = self._build_request_async(
            method="GET",
            path="/portal/management/usage",
            base_url=base_url,
            url_variables=None,
            request=request,
            request_body_required=False,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=self._build_headers(http_headers, manage_key),
            security=None,
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
                operation_id="getCreditsUsage",
                oauth2_scopes=None,
                security_source=None,
            ),
            request=req,
            error_status_codes=["400", "401", "403", "4XX", "500", "5XX"],
            retry_config=retry_config,
        )

        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(CreditsUsageResponse, http_res)

        return await self._handle_error_response_async(http_res)
