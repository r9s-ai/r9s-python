from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from r9s import errors
from r9s import R9S as GeneratedR9S
from r9s.client import R9S


def _json_response(status_code: int, payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode(),
    )


class _HttpClientStub:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.last_request: httpx.Request | None = None

    def build_request(self, method: str, url: Any, **kwargs: Any) -> httpx.Request:
        kwargs.pop("timeout", None)
        return httpx.Request(method, url, **kwargs)

    def send(
        self, request: httpx.Request, *, stream: bool = False, **_: Any
    ) -> httpx.Response:
        self.last_request = request
        return httpx.Response(
            self.response.status_code,
            headers=self.response.headers,
            content=self.response.content,
            request=request,
        )

    def close(self) -> None:
        return None


class _AsyncHttpClientStub:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.last_request: httpx.Request | None = None

    def build_request(self, method: str, url: Any, **kwargs: Any) -> httpx.Request:
        kwargs.pop("timeout", None)
        return httpx.Request(method, url, **kwargs)

    async def send(
        self, request: httpx.Request, *, stream: bool = False, **_: Any
    ) -> httpx.Response:
        self.last_request = request
        return httpx.Response(
            self.response.status_code,
            headers=self.response.headers,
            content=self.response.content,
            request=request,
        )

    async def aclose(self) -> None:
        return None


def _sdk(
    response: httpx.Response,
    *,
    manage_key: str | None = "sk_mg_secret",
) -> tuple[R9S, _HttpClientStub]:
    client = _HttpClientStub(response)
    async_client = _AsyncHttpClientStub(response)
    r9s = R9S(
        api_key="secret-key",
        manage_key=manage_key,
        server_url="https://api.r9s.ai/v1",
        client=client,
        async_client=async_client,
    )
    return r9s, client


def test_account_get_uses_manage_key_and_default_portal_base_url() -> None:
    payload = {
        "data": {
            "records": [{"timestamp": 1735689600, "tokens": 1024, "model": "gpt-4o-mini"}],
            "total_tokens": 1024,
        }
    }
    r9s, client = _sdk(_json_response(200, payload))

    response = r9s.account.usage(start_time=1735689600, end_time=1736294400)

    assert client.last_request is not None
    assert (
        str(client.last_request.url)
        == "https://portal-api.r9s.ai/api/v1/portal/management/usage"
        "?start_time=1735689600&end_time=1736294400"
    )
    assert client.last_request.headers["Authorization"] == "Bearer sk_mg_secret"
    assert response.data is not None
    assert response.data.total_tokens == 1024
    assert response.data.records is not None
    assert response.data.records[0].model == "gpt-4o-mini"


def test_account_get_accepts_iso_time_strings() -> None:
    r9s, client = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))

    r9s.account.usage(
        start_time="2025-01-01T00:00:00+00:00",
        end_time="2025-01-08T00:00:00+00:00",
    )

    assert client.last_request is not None
    parsed = parse_qs(urlparse(str(client.last_request.url)).query)
    assert parsed["start_time"] == ["1735689600"]
    assert parsed["end_time"] == ["1736294400"]


def test_account_get_supports_server_url_override() -> None:
    r9s, client = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))

    r9s.account.usage(
        start_time=1735689600,
        end_time=1736294400,
        server_url="https://example.com/api/v1",
    )

    assert client.last_request is not None
    assert str(client.last_request.url).startswith(
        "https://example.com/api/v1/portal/management/usage"
    )


def test_account_get_uses_default_centered_seven_day_window_when_omitted() -> None:
    r9s, client = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))

    before = datetime.now().astimezone()
    r9s.account.usage()
    after = datetime.now().astimezone()

    assert client.last_request is not None
    parsed = parse_qs(urlparse(str(client.last_request.url)).query)
    start_time = int(parsed["start_time"][0])
    end_time = int(parsed["end_time"][0])

    expected_start_before = int(
        datetime.combine(
            before.date(), datetime.min.time(), tzinfo=before.tzinfo
        ).timestamp()
    ) - 3 * 24 * 60 * 60
    expected_end_before = int(
        datetime.combine(
            before.date(), datetime.min.time(), tzinfo=before.tzinfo
        ).timestamp()
    ) + 4 * 24 * 60 * 60
    expected_start_after = int(
        datetime.combine(
            after.date(), datetime.min.time(), tzinfo=after.tzinfo
        ).timestamp()
    ) - 3 * 24 * 60 * 60
    expected_end_after = int(
        datetime.combine(
            after.date(), datetime.min.time(), tzinfo=after.tzinfo
        ).timestamp()
    ) + 4 * 24 * 60 * 60

    assert start_time in {expected_start_before, expected_start_after}
    assert end_time in {expected_end_before, expected_end_after}


def test_account_get_requires_manage_key() -> None:
    r9s, _ = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}), manage_key=None)

    with pytest.raises(ValueError, match="manage_key is required"):
        r9s.account.usage(start_time=1735689600, end_time=1736294400)


def test_account_get_rejects_partial_time_range() -> None:
    r9s, _ = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))

    with pytest.raises(ValueError, match="must both be provided"):
        r9s.account.usage(start_time=1735689600)


def test_account_get_accepts_datetime_objects() -> None:
    r9s, client = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))

    r9s.account.usage(
        start_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2025, 1, 8, tzinfo=timezone.utc),
    )

    assert client.last_request is not None
    parsed = parse_qs(urlparse(str(client.last_request.url)).query)
    assert parsed["start_time"] == ["1735689600"]
    assert parsed["end_time"] == ["1736294400"]


def test_account_usage_allows_manage_key_override() -> None:
    r9s, client = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))

    r9s.account.usage(
        start_time=1735689600,
        end_time=1736294400,
        manage_key="sk_mg_override",
    )

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer sk_mg_override"


def test_account_balance_uses_manage_key_and_default_portal_base_url() -> None:
    payload = {
        "meta": {"code": 0, "message": "", "request_id": "CffamfvUaPO1NqCuE6k8Ef9eoUTQr13C"},
        "data": {
            "balance": 470.010481,
            "balance_str": "470.010481",
            "coupon_balance": 0,
            "currency_code": "USD",
            "credit_limit": 0,
            "total_coupon_amount": 0,
        },
    }
    r9s, client = _sdk(_json_response(200, payload))

    response = r9s.account.balance()

    assert client.last_request is not None
    assert (
        str(client.last_request.url)
        == "https://portal-api.r9s.ai/api/v1/portal/management/balance"
    )
    assert client.last_request.headers["Authorization"] == "Bearer sk_mg_secret"
    assert response.data is not None
    assert response.data.balance == 470.010481
    assert response.data.balance_str == "470.010481"
    assert response.data.currency_code == "USD"


def test_account_balance_supports_server_url_override() -> None:
    r9s, client = _sdk(_json_response(200, {"data": {"balance": 1, "currency_code": "USD"}}))

    r9s.account.balance(server_url="https://example.com/api/v1")

    assert client.last_request is not None
    assert str(client.last_request.url) == "https://example.com/api/v1/portal/management/balance"


def test_account_balance_requires_manage_key() -> None:
    r9s, _ = _sdk(_json_response(200, {"data": {"balance": 1}}), manage_key=None)

    with pytest.raises(ValueError, match="manage_key is required"):
        r9s.account.balance()


def test_account_balance_allows_manage_key_override() -> None:
    r9s, client = _sdk(_json_response(200, {"data": {"balance": 1, "currency_code": "USD"}}))

    r9s.account.balance(manage_key="sk_mg_override")

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer sk_mg_override"


def test_account_balance_401_parses_portal_meta_auth_error_shape() -> None:
    r9s, _ = _sdk(
        _json_response(
            401,
            {
                "meta": {
                    "code": 401,
                    "message": "Invalid API key format",
                    "request_id": "jvkQLEFhtEm1nWcl0AbtMLQmdKPlPNci",
                },
                "data": None,
            },
        )
    )

    with pytest.raises(errors.AuthenticationError) as exc_info:
        r9s.account.balance()

    err = exc_info.value
    assert err.message == "Invalid API key format"
    assert err.data.error.request_id == "jvkQLEFhtEm1nWcl0AbtMLQmdKPlPNci"
    assert err.data.error.code == 401


def test_account_usage_manage_key_override_works_without_client_manage_key() -> None:
    r9s, client = _sdk(
        _json_response(200, {"data": {"records": [], "total_tokens": 0}}),
        manage_key=None,
    )

    r9s.account.usage(
        start_time=1735689600,
        end_time=1736294400,
        manage_key="sk_mg_override",
    )

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer sk_mg_override"


def test_generated_r9s_exposes_account_sub_sdk() -> None:
    client = _HttpClientStub(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))
    async_client = _AsyncHttpClientStub(
        _json_response(200, {"data": {"records": [], "total_tokens": 0}})
    )
    r9s = GeneratedR9S(
        api_key="secret-key",
        manage_key="sk_mg_secret",
        client=client,
        async_client=async_client,
    )

    r9s.account.usage(start_time=1735689600, end_time=1736294400)

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer sk_mg_secret"


def test_account_get_401_parses_portal_meta_auth_error_shape() -> None:
    r9s, _ = _sdk(
        _json_response(
            401,
            {
                "meta": {
                    "code": 401,
                    "message": "API key not found",
                    "request_id": "7Decb7JmukO2zxHeLMhkGtogj1vK9QJs",
                },
                "data": None,
            },
        )
    )

    with pytest.raises(errors.AuthenticationError) as exc_info:
        r9s.account.usage(start_time=1735689600, end_time=1736294400)

    err = exc_info.value
    assert err.message == "API key not found"
    assert err.data.error.request_id == "7Decb7JmukO2zxHeLMhkGtogj1vK9QJs"
    assert err.data.error.code == 401


@pytest.mark.asyncio
async def test_account_get_async_401_parses_portal_meta_auth_error_shape() -> None:
    r9s, _ = _sdk(
        _json_response(
            401,
            {
                "meta": {
                    "code": 401,
                    "message": "API key not found",
                    "request_id": "7Decb7JmukO2zxHeLMhkGtogj1vK9QJs",
                },
                "data": None,
            },
        )
    )

    with pytest.raises(errors.AuthenticationError) as exc_info:
        await r9s.account.usage_async(start_time=1735689600, end_time=1736294400)

    err = exc_info.value
    assert err.message == "API key not found"
    assert err.data.error.request_id == "7Decb7JmukO2zxHeLMhkGtogj1vK9QJs"
    assert err.data.error.code == 401


@pytest.mark.asyncio
async def test_account_usage_async_allows_manage_key_override() -> None:
    r9s, _ = _sdk(_json_response(200, {"data": {"records": [], "total_tokens": 0}}))

    await r9s.account.usage_async(
        start_time=1735689600,
        end_time=1736294400,
        manage_key="sk_mg_override",
    )

    async_client = r9s.sdk_configuration.async_client
    assert async_client is not None
    assert async_client.last_request is not None
    assert async_client.last_request.headers["Authorization"] == "Bearer sk_mg_override"


@pytest.mark.asyncio
async def test_account_balance_async_401_parses_portal_meta_auth_error_shape() -> None:
    r9s, _ = _sdk(
        _json_response(
            401,
            {
                "meta": {
                    "code": 401,
                    "message": "Invalid API key format",
                    "request_id": "jvkQLEFhtEm1nWcl0AbtMLQmdKPlPNci",
                },
                "data": None,
            },
        )
    )

    with pytest.raises(errors.AuthenticationError) as exc_info:
        await r9s.account.balance_async()

    err = exc_info.value
    assert err.message == "Invalid API key format"
    assert err.data.error.request_id == "jvkQLEFhtEm1nWcl0AbtMLQmdKPlPNci"
    assert err.data.error.code == 401
