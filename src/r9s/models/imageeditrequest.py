"""Image edit request model for inpainting operations."""

from __future__ import annotations

import io

import pydantic
from r9s.types import BaseModel
from r9s.utils import FieldMetadata, MultipartFormMetadata
from typing import IO, Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict


class ImageFileTypedDict(TypedDict):
    file_name: str
    content: Union[bytes, IO[bytes], io.BufferedReader]
    content_type: NotRequired[str]


class ImageFile(BaseModel):
    """Image file for upload."""

    file_name: Annotated[
        str, pydantic.Field(alias="fileName"), FieldMetadata(multipart=True)
    ]

    content: Annotated[
        Union[bytes, IO[bytes], io.BufferedReader],
        pydantic.Field(alias=""),
        FieldMetadata(multipart=MultipartFormMetadata(content=True)),
    ]

    content_type: Annotated[
        Optional[str],
        pydantic.Field(alias="Content-Type"),
        FieldMetadata(multipart=True),
    ] = None


ImageEditResponseFormat = Literal["url", "b64_json"]

ImageEditSize = Literal["256x256", "512x512", "1024x1024"]


class ImageEditRequestTypedDict(TypedDict):
    image: ImageFileTypedDict
    prompt: str
    model: NotRequired[str]
    mask: NotRequired[ImageFileTypedDict]
    n: NotRequired[int]
    size: NotRequired[ImageEditSize]
    response_format: NotRequired[ImageEditResponseFormat]
    user: NotRequired[str]


class ImageEditRequest(BaseModel):
    """Request model for image editing (inpainting) operations."""

    image: Annotated[
        ImageFile, FieldMetadata(multipart=MultipartFormMetadata(file=True))
    ]
    r"""The image to edit. Must be PNG, less than 4MB, and square."""

    prompt: Annotated[str, FieldMetadata(multipart=True)]
    r"""A text description of the desired image(s)."""

    model: Annotated[Optional[str], FieldMetadata(multipart=True)] = None
    r"""The model to use for image editing."""

    mask: Annotated[
        Optional[ImageFile],
        FieldMetadata(multipart=MultipartFormMetadata(file=True)),
    ] = None
    r"""PNG with transparent areas indicating where to edit."""

    n: Annotated[Optional[int], FieldMetadata(multipart=True)] = 1
    r"""Number of images to generate. Range: 1-10."""

    size: Annotated[Optional[ImageEditSize], FieldMetadata(multipart=True)] = (
        "1024x1024"
    )
    r"""The size of the generated images."""

    response_format: Annotated[
        Optional[ImageEditResponseFormat], FieldMetadata(multipart=True)
    ] = "url"
    r"""Format of returned images: 'url' or 'b64_json'."""

    user: Annotated[Optional[str], FieldMetadata(multipart=True)] = None
    r"""Unique identifier for end-user tracking."""
