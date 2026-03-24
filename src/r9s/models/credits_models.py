from __future__ import annotations

from typing import Any, Optional

from r9s.types import BaseModel
from r9s.utils import FieldMetadata, QueryParamMetadata
from typing_extensions import Annotated
from typing_extensions import TypedDict


class CreditsUsageRecordTypedDict(TypedDict, total=False):
    timestamp: int
    tokens: int
    model: str


class CreditsUsageRecord(BaseModel):
    timestamp: Optional[int] = None
    r"""Record timestamp as a Unix timestamp in seconds"""

    tokens: Optional[int] = None
    r"""Tokens consumed for the record"""

    model: Optional[str] = None
    r"""Model name for the record"""


class CreditsUsageDataTypedDict(TypedDict, total=False):
    records: list[CreditsUsageRecordTypedDict]
    total_tokens: int


class CreditsUsageData(BaseModel):
    records: Optional[list[CreditsUsageRecord]] = None

    total_tokens: Optional[int] = None
    r"""Total tokens consumed in the queried range"""


class CreditsUsageResponseTypedDict(TypedDict, total=False):
    data: CreditsUsageDataTypedDict


class CreditsUsageResponse(BaseModel):
    data: Optional[CreditsUsageData] = None

    model_config = {"extra": "allow"}


class GetCreditsUsageRequestTypedDict(TypedDict):
    start_time: int
    end_time: int


class GetCreditsUsageRequest(BaseModel):
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
