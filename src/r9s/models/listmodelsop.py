from __future__ import annotations

from r9s.types import BaseModel
from r9s.utils import FieldMetadata, QueryParamMetadata
from typing import List, Optional
from typing_extensions import Annotated, TypedDict


class ListModelsRequestTypedDict(TypedDict, total=False):
    expand: str
    r"""Comma-separated expand fields."""

    filter: List[str]
    r"""Filter rules. Repeated query parameter."""


class ListModelsRequest(BaseModel):
    expand: Annotated[
        Optional[str],
        FieldMetadata(query=QueryParamMetadata(style="form", explode=True)),
    ] = None
    r"""Comma-separated expand fields."""

    filter: Annotated[
        Optional[List[str]],
        FieldMetadata(query=QueryParamMetadata(style="form", explode=True)),
    ] = None
    r"""Filter rules. Repeated query parameter."""
