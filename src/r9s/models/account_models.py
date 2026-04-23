from __future__ import annotations

from typing import Any, Optional

from r9s.types import BaseModel
from r9s.utils import FieldMetadata, QueryParamMetadata
from typing_extensions import Annotated
from typing_extensions import TypedDict


class AccountUsageRecordTypedDict(TypedDict, total=False):
    timestamp: int
    tokens: int
    model: str


class AccountUsageRecord(BaseModel):
    timestamp: Optional[int] = None
    r"""Record timestamp as a Unix timestamp in seconds"""

    tokens: Optional[int] = None
    r"""Tokens consumed for the record"""

    model: Optional[str] = None
    r"""Model name for the record"""


class AccountUsageDataTypedDict(TypedDict, total=False):
    records: list[AccountUsageRecordTypedDict]
    total_tokens: int


class AccountUsageData(BaseModel):
    records: Optional[list[AccountUsageRecord]] = None

    total_tokens: Optional[int] = None
    r"""Total tokens consumed in the queried range"""


class AccountUsageResponseTypedDict(TypedDict, total=False):
    data: AccountUsageDataTypedDict


class AccountUsageResponse(BaseModel):
    data: Optional[AccountUsageData] = None

    model_config = {"extra": "allow"}


class AccountBalanceDataTypedDict(TypedDict, total=False):
    balance: float
    balance_str: str
    coupon_balance: float
    currency_code: str
    credit_limit: float
    total_coupon_amount: float


class AccountBalanceData(BaseModel):
    balance: Optional[float] = None
    r"""Current account balance"""

    balance_str: Optional[str] = None
    r"""String representation of the current account balance"""

    coupon_balance: Optional[float] = None
    r"""Currently available coupon balance"""

    currency_code: Optional[str] = None
    r"""Currency code for the returned balances"""

    credit_limit: Optional[float] = None
    r"""Credit limit available to the account"""

    total_coupon_amount: Optional[float] = None
    r"""Total coupon amount associated with the account"""


class AccountBalanceResponseTypedDict(TypedDict, total=False):
    data: AccountBalanceDataTypedDict


class AccountBalanceResponse(BaseModel):
    data: Optional[AccountBalanceData] = None

    model_config = {"extra": "allow"}


class GetAccountUsageRequestTypedDict(TypedDict):
    start_time: int
    end_time: int


class GetAccountUsageRequest(BaseModel):
    start_time: Annotated[
        int,
        FieldMetadata(query=QueryParamMetadata(style="form", explode=True)),
    ]
    r"""Start of the query range as a Unix timestamp in seconds"""

    end_time: Annotated[
        int,
        FieldMetadata(query=QueryParamMetadata(style="form", explode=True)),
    ]
    r"""End of the query range as a Unix timestamp in seconds"""

    model_config = {"extra": "allow"}
