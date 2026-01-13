"""Tests for image editing (inpainting) functionality."""

from __future__ import annotations

from typing import Any

from r9s.models.imageeditrequest import (
    ImageEditRequest,
    ImageEditResponseFormat,
    ImageEditSize,
    ImageFile,
    ImageFileTypedDict,
)


class TestImageFileModel:
    """Tests for ImageFile model."""

    def test_image_file_with_bytes(self) -> None:
        """ImageFile accepts bytes content."""
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        file = ImageFile(
            file_name="test.png",
            content=png_bytes,
            content_type="image/png",
        )
        assert file.file_name == "test.png"
        assert file.content == png_bytes
        assert file.content_type == "image/png"

    def test_image_file_with_buffered_reader(self, tmp_path: Any) -> None:
        """ImageFile accepts BufferedReader content."""
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        test_file = tmp_path / "test.png"
        test_file.write_bytes(png_bytes)

        with open(test_file, "rb") as f:
            file = ImageFile(
                file_name="test.png",
                content=f,
            )
            assert file.file_name == "test.png"
            assert file.content_type is None  # Optional

    def test_image_file_from_typed_dict(self) -> None:
        """ImageFile can be created from TypedDict."""
        data: ImageFileTypedDict = {
            "file_name": "image.png",
            "content": b"\x89PNG\r\n\x1a\n",
            "content_type": "image/png",
        }
        file = ImageFile(**data)
        assert file.file_name == "image.png"

    def test_image_file_without_content_type(self) -> None:
        """ImageFile content_type is optional."""
        file = ImageFile(
            file_name="test.png",
            content=b"\x89PNG\r\n\x1a\n",
        )
        assert file.file_name == "test.png"
        assert file.content_type is None


class TestImageEditRequestModel:
    """Tests for ImageEditRequest model."""

    def test_minimal_request(self) -> None:
        """Request with only required fields."""
        image = ImageFile(
            file_name="test.png",
            content=b"\x89PNG\r\n\x1a\n",
        )
        request = ImageEditRequest(
            image=image,
            prompt="Add a hat",
        )
        assert request.prompt == "Add a hat"
        assert request.n == 1  # default
        assert request.size == "1024x1024"  # default
        assert request.response_format == "url"  # default
        assert request.mask is None
        assert request.model is None
        assert request.user is None

    def test_full_request(self) -> None:
        """Request with all fields populated."""
        image = ImageFile(file_name="img.png", content=b"image_data")
        mask = ImageFile(file_name="mask.png", content=b"mask_data")

        request = ImageEditRequest(
            image=image,
            prompt="Replace background",
            model="dall-e-2",
            mask=mask,
            n=3,
            size="512x512",
            response_format="b64_json",
            user="user-123",
        )
        assert request.model == "dall-e-2"
        assert request.mask is not None
        assert request.n == 3
        assert request.size == "512x512"
        assert request.response_format == "b64_json"
        assert request.user == "user-123"

    def test_size_literal_values(self) -> None:
        """Size field accepts valid literals."""
        image = ImageFile(file_name="t.png", content=b"x")

        for size in ["256x256", "512x512", "1024x1024"]:
            req = ImageEditRequest(image=image, prompt="test", size=size)  # type: ignore
            assert req.size == size

    def test_response_format_literal_values(self) -> None:
        """response_format accepts 'url' or 'b64_json'."""
        image = ImageFile(file_name="t.png", content=b"x")

        for fmt in ["url", "b64_json"]:
            req = ImageEditRequest(image=image, prompt="test", response_format=fmt)  # type: ignore
            assert req.response_format == fmt

    def test_n_defaults_to_one(self) -> None:
        """n parameter defaults to 1."""
        image = ImageFile(file_name="t.png", content=b"x")
        request = ImageEditRequest(image=image, prompt="test")
        assert request.n == 1

    def test_model_is_optional(self) -> None:
        """model parameter is optional and defaults to None."""
        image = ImageFile(file_name="t.png", content=b"x")
        request = ImageEditRequest(image=image, prompt="test")
        assert request.model is None

    def test_user_is_optional(self) -> None:
        """user parameter is optional and defaults to None."""
        image = ImageFile(file_name="t.png", content=b"x")
        request = ImageEditRequest(image=image, prompt="test")
        assert request.user is None

    def test_mask_is_optional(self) -> None:
        """mask parameter is optional and defaults to None."""
        image = ImageFile(file_name="t.png", content=b"x")
        request = ImageEditRequest(image=image, prompt="test")
        assert request.mask is None

    def test_request_with_mask(self) -> None:
        """Request can include a mask file."""
        image = ImageFile(file_name="image.png", content=b"image_content")
        mask = ImageFile(file_name="mask.png", content=b"mask_content")

        request = ImageEditRequest(
            image=image,
            prompt="Edit the image",
            mask=mask,
        )

        assert request.mask is not None
        assert request.mask.file_name == "mask.png"


class TestImageEditTypes:
    """Tests for ImageEdit type aliases."""

    def test_image_edit_size_values(self) -> None:
        """ImageEditSize should accept valid size strings."""
        valid_sizes: list[ImageEditSize] = ["256x256", "512x512", "1024x1024"]
        for size in valid_sizes:
            assert size in ["256x256", "512x512", "1024x1024"]

    def test_image_edit_response_format_values(self) -> None:
        """ImageEditResponseFormat should accept valid format strings."""
        valid_formats: list[ImageEditResponseFormat] = ["url", "b64_json"]
        for fmt in valid_formats:
            assert fmt in ["url", "b64_json"]


class TestImageEditRequestTypedDict:
    """Tests for ImageEditRequestTypedDict."""

    def test_typed_dict_minimal(self) -> None:
        """TypedDict with only required fields."""
        from r9s.models.imageeditrequest import ImageEditRequestTypedDict

        data: ImageEditRequestTypedDict = {
            "image": {"file_name": "test.png", "content": b"data"},
            "prompt": "Edit this",
        }
        assert data["prompt"] == "Edit this"

    def test_typed_dict_full(self) -> None:
        """TypedDict with all fields."""
        from r9s.models.imageeditrequest import ImageEditRequestTypedDict

        data: ImageEditRequestTypedDict = {
            "image": {"file_name": "test.png", "content": b"data"},
            "prompt": "Edit this",
            "model": "dall-e-2",
            "mask": {"file_name": "mask.png", "content": b"mask"},
            "n": 2,
            "size": "512x512",
            "response_format": "b64_json",
            "user": "user-123",
        }
        assert data["model"] == "dall-e-2"
        assert data["n"] == 2
