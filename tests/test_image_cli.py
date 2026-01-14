"""Tests for image CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestImageCliParser:
    """Tests for image CLI argument parsing."""

    def get_parser(self) -> argparse.ArgumentParser:
        """Get the CLI parser."""
        from r9s.cli_tools.cli import build_parser
        return build_parser()

    def test_images_help(self) -> None:
        """images command shows help (exits with 0)."""
        parser = self.get_parser()
        # --help causes SystemExit(0)
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["images", "generate", "--help"])
        assert exc_info.value.code == 0

    def test_generate_minimal(self) -> None:
        """Generate with just a prompt."""
        parser = self.get_parser()
        args = parser.parse_args(["images", "generate", "A beautiful sunset"])
        assert args.prompt == "A beautiful sunset"
        assert args.output is None
        assert args.model is None
        assert args.n == 1

    def test_generate_with_output(self) -> None:
        """Generate with output file."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "A cat", "-o", "cat.png"
        ])
        assert args.prompt == "A cat"
        assert args.output == "cat.png"

    def test_generate_with_model_and_size(self) -> None:
        """Generate with model and size options."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "A dragon",
            "-m", "dall-e-3",
            "-s", "1024x1792"
        ])
        assert args.model == "dall-e-3"
        assert args.size == "1024x1792"

    def test_generate_with_quality(self) -> None:
        """Generate with quality option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Art", "-q", "hd"
        ])
        assert args.quality == "hd"

    def test_generate_with_n(self) -> None:
        """Generate multiple images."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Cars", "-n", "5"
        ])
        assert args.n == 5

    def test_generate_with_style(self) -> None:
        """Generate with style option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Landscape", "--style", "natural"
        ])
        assert args.style == "natural"

    def test_generate_with_negative_prompt(self) -> None:
        """Generate with negative prompt (Qwen)."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Forest",
            "--negative-prompt", "people,buildings"
        ])
        assert args.negative_prompt == "people,buildings"

    def test_generate_with_seed(self) -> None:
        """Generate with seed for reproducibility."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Dragon", "--seed", "12345"
        ])
        assert args.seed == 12345

    def test_generate_with_prompt_extend(self) -> None:
        """Generate with prompt_extend flag."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Art", "--prompt-extend"
        ])
        assert args.prompt_extend is True

    def test_generate_with_no_prompt_extend(self) -> None:
        """Generate with --no-prompt-extend flag."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Art", "--no-prompt-extend"
        ])
        assert args.prompt_extend is False

    def test_generate_with_watermark(self) -> None:
        """Generate with watermark flag."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Art", "--watermark"
        ])
        assert args.watermark is True

    def test_generate_with_no_watermark(self) -> None:
        """Generate with --no-watermark flag."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Art", "--no-watermark"
        ])
        assert args.watermark is False

    def test_generate_with_format_url(self) -> None:
        """Generate with url format."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Cat", "-f", "url"
        ])
        assert args.format == "url"

    def test_generate_with_format_b64(self) -> None:
        """Generate with b64 format."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Cat", "-f", "b64"
        ])
        assert args.format == "b64"

    def test_generate_with_json_output(self) -> None:
        """Generate with JSON output flag."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Cat", "--json"
        ])
        assert args.json is True

    def test_generate_all_options(self) -> None:
        """Generate with all options."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "A majestic lion",
            "-o", "lion.png",
            "-m", "wanx-v1",
            "-s", "1024x1024",
            "-q", "hd",
            "-n", "2",
            "--negative-prompt", "cartoon",
            "--seed", "42",
            "--prompt-extend",
            "--watermark",
        ])
        assert args.prompt == "A majestic lion"
        assert args.output == "lion.png"
        assert args.model == "wanx-v1"
        assert args.size == "1024x1024"
        assert args.quality == "hd"
        assert args.n == 2
        assert args.negative_prompt == "cartoon"
        assert args.seed == 42
        assert args.prompt_extend is True
        assert args.watermark is True

    def test_generate_with_open(self) -> None:
        """Generate with --open flag."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Cat", "-o", "cat.png", "--open"
        ])
        assert args.open is True

    def test_generate_with_background(self) -> None:
        """Generate with --background option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Logo", "--background", "transparent"
        ])
        assert args.background == "transparent"

    def test_generate_with_output_format(self) -> None:
        """Generate with --output-format option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "Photo", "--output-format", "webp"
        ])
        assert args.output_format == "webp"

    def test_generate_new_options_combined(self) -> None:
        """Generate with all new options combined."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "generate", "A logo",
            "-o", "logo.png",
            "--open",
            "--background", "transparent",
            "--output-format", "png",
        ])
        assert args.open is True
        assert args.background == "transparent"
        assert args.output_format == "png"

    def test_edit_minimal(self) -> None:
        """Edit with required arguments."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "photo.png", "Add a hat"
        ])
        assert args.image == "photo.png"
        assert args.prompt == "Add a hat"
        assert args.output is None
        assert args.mask is None

    def test_edit_with_output(self) -> None:
        """Edit with output file."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "input.png", "Make it blue",
            "-o", "output.png"
        ])
        assert args.output == "output.png"

    def test_edit_with_mask(self) -> None:
        """Edit with mask file."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "photo.png", "Replace background",
            "--mask", "mask.png"
        ])
        assert args.mask == "mask.png"

    def test_edit_with_model(self) -> None:
        """Edit with model option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "photo.png", "Edit",
            "-m", "dall-e-2"
        ])
        assert args.model == "dall-e-2"

    def test_edit_with_size(self) -> None:
        """Edit with size option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "photo.png", "Edit",
            "-s", "512x512"
        ])
        assert args.size == "512x512"

    def test_edit_with_n(self) -> None:
        """Edit generating multiple variations."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "photo.png", "Variations",
            "-n", "3"
        ])
        assert args.n == 3

    def test_edit_all_options(self) -> None:
        """Edit with all options."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "input.png", "Add sunglasses",
            "-o", "result.png",
            "--mask", "face_mask.png",
            "-m", "dall-e-2",
            "-s", "1024x1024",
            "-n", "2",
            "-f", "b64",
            "--json",
        ])
        assert args.image == "input.png"
        assert args.prompt == "Add sunglasses"
        assert args.output == "result.png"
        assert args.mask == "face_mask.png"
        assert args.model == "dall-e-2"
        assert args.size == "1024x1024"
        assert args.n == 2
        assert args.format == "b64"
        assert args.json is True

    def test_edit_with_open(self) -> None:
        """Edit with --open flag."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "photo.png", "Edit", "-o", "out.png", "--open"
        ])
        assert args.open is True

    def test_edit_with_background(self) -> None:
        """Edit with --background option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "logo.png", "Remove bg", "--background", "transparent"
        ])
        assert args.background == "transparent"

    def test_edit_with_output_format(self) -> None:
        """Edit with --output-format option."""
        parser = self.get_parser()
        args = parser.parse_args([
            "images", "edit", "photo.png", "Enhance", "--output-format", "jpeg"
        ])
        assert args.output_format == "jpeg"


class TestImageCliHelpers:
    """Tests for image CLI helper functions."""

    def test_read_image_file_not_found(self, tmp_path: Path) -> None:
        """read_image_file raises SystemExit for missing file."""
        from r9s.cli_tools.image_cli import read_image_file

        with pytest.raises(SystemExit):
            read_image_file(tmp_path / "nonexistent.png")

    def test_read_image_file_success(self, tmp_path: Path) -> None:
        """read_image_file returns file contents."""
        from r9s.cli_tools.image_cli import read_image_file

        test_file = tmp_path / "test.png"
        test_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        test_file.write_bytes(test_data)

        result = read_image_file(test_file)
        assert result == test_data

    def test_save_image_creates_directories(self, tmp_path: Path) -> None:
        """save_image creates parent directories."""
        from r9s.cli_tools.image_cli import save_image

        output_path = tmp_path / "subdir" / "nested" / "image.png"
        test_data = b"\x89PNG\r\n\x1a\n"

        save_image(test_data, output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == test_data

    def test_generate_output_filename_single(self, tmp_path: Path) -> None:
        """generate_output_filename for single image."""
        from r9s.cli_tools.image_cli import generate_output_filename

        result = generate_output_filename(tmp_path, 0, 1)
        assert result == tmp_path / "image.png"

    def test_generate_output_filename_multiple(self, tmp_path: Path) -> None:
        """generate_output_filename for multiple images."""
        from r9s.cli_tools.image_cli import generate_output_filename

        assert generate_output_filename(tmp_path, 0, 3) == tmp_path / "image_1.png"
        assert generate_output_filename(tmp_path, 1, 3) == tmp_path / "image_2.png"
        assert generate_output_filename(tmp_path, 2, 3) == tmp_path / "image_3.png"

    def test_generate_output_filename_with_extension(self, tmp_path: Path) -> None:
        """generate_output_filename with custom extension."""
        from r9s.cli_tools.image_cli import generate_output_filename

        assert generate_output_filename(tmp_path, 0, 1, "webp") == tmp_path / "image.webp"
        assert generate_output_filename(tmp_path, 0, 2, "jpeg") == tmp_path / "image_1.jpeg"

    def test_open_file_macos(self, tmp_path: Path) -> None:
        """open_file uses 'open' on macOS."""
        from r9s.cli_tools.image_cli import open_file

        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"test")

        with patch("r9s.cli_tools.image_cli.platform.system", return_value="Darwin"):
            with patch("r9s.cli_tools.image_cli.subprocess.run") as mock_run:
                open_file(test_file)
                mock_run.assert_called_once_with(["open", str(test_file)], check=True)

    def test_open_file_linux(self, tmp_path: Path) -> None:
        """open_file uses 'xdg-open' on Linux."""
        from r9s.cli_tools.image_cli import open_file

        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"test")

        with patch("r9s.cli_tools.image_cli.platform.system", return_value="Linux"):
            with patch("r9s.cli_tools.image_cli.subprocess.run") as mock_run:
                open_file(test_file)
                mock_run.assert_called_once_with(["xdg-open", str(test_file)], check=True)

    def test_open_files_opens_all(self, tmp_path: Path) -> None:
        """open_files opens all provided files."""
        from r9s.cli_tools.image_cli import open_files

        files = [tmp_path / "a.png", tmp_path / "b.png"]
        for f in files:
            f.write_bytes(b"test")

        with patch("r9s.cli_tools.image_cli.open_file") as mock_open:
            open_files(files)
            assert mock_open.call_count == 2


class TestImageGenerateHandler:
    """Tests for handle_image_generate function."""

    def test_generate_no_prompt_no_stdin_fails(self) -> None:
        """Generate without prompt and not piped fails."""
        from r9s.cli_tools.image_cli import handle_image_generate

        args = argparse.Namespace(
            prompt=None,
            output=None,
            model=None,
            size=None,
            quality=None,
            n=1,
            style=None,
            negative_prompt=None,
            seed=None,
            prompt_extend=None,
            watermark=None,
            format=None,
            json=False,
        )

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with pytest.raises(SystemExit):
                handle_image_generate(args)

    def test_generate_success_prints_url(self, capsys: Any) -> None:
        """Generate successfully prints URL."""
        from r9s.cli_tools.image_cli import handle_image_generate

        args = argparse.Namespace(
            prompt="A cat",
            output=None,
            model=None,
            size=None,
            quality=None,
            n=1,
            style=None,
            negative_prompt=None,
            seed=None,
            prompt_extend=None,
            watermark=None,
            format=None,
            json=False,
        )

        # Mock the client and response
        mock_image = MagicMock()
        mock_image.url = "https://example.com/image.png"
        mock_image.b64_json = None
        mock_image.revised_prompt = None

        mock_response = MagicMock()
        mock_response.data = [mock_image]
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.images.create.return_value = mock_response

        with patch("r9s.cli_tools.image_cli.get_client", return_value=mock_client):
            with patch("r9s.cli_tools.image_cli.LoadingSpinner"):
                handle_image_generate(args)

        captured = capsys.readouterr()
        assert "https://example.com/image.png" in captured.out

    def test_generate_saves_to_file(self, tmp_path: Path) -> None:
        """Generate saves image to file when -o specified."""
        from r9s.cli_tools.image_cli import handle_image_generate
        import base64

        output_file = tmp_path / "result.png"
        test_image_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50

        args = argparse.Namespace(
            prompt="A cat",
            output=str(output_file),
            model=None,
            size=None,
            quality=None,
            n=1,
            style=None,
            negative_prompt=None,
            seed=None,
            prompt_extend=None,
            watermark=None,
            format=None,
            json=False,
        )

        mock_image = MagicMock()
        mock_image.url = None
        mock_image.b64_json = base64.b64encode(test_image_data).decode()
        mock_image.revised_prompt = None

        mock_response = MagicMock()
        mock_response.data = [mock_image]
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.images.create.return_value = mock_response

        with patch("r9s.cli_tools.image_cli.get_client", return_value=mock_client):
            with patch("r9s.cli_tools.image_cli.LoadingSpinner"):
                handle_image_generate(args)

        assert output_file.exists()
        assert output_file.read_bytes() == test_image_data

    def test_generate_passes_extended_params(self) -> None:
        """Generate passes extended parameters to API."""
        from r9s.cli_tools.image_cli import handle_image_generate

        args = argparse.Namespace(
            prompt="A forest",
            output=None,
            model="wanx-v1",
            size="1024x1024",
            quality="hd",
            n=1,
            style=None,
            negative_prompt="people,cars",
            seed=12345,
            prompt_extend=True,
            watermark=False,
            format=None,
            json=False,
        )

        mock_image = MagicMock()
        mock_image.url = "https://example.com/image.png"
        mock_image.b64_json = None
        mock_image.revised_prompt = None

        mock_response = MagicMock()
        mock_response.data = [mock_image]
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.images.create.return_value = mock_response

        with patch("r9s.cli_tools.image_cli.get_client", return_value=mock_client):
            with patch("r9s.cli_tools.image_cli.LoadingSpinner"):
                handle_image_generate(args)

        # Verify the create call included extended params
        call_kwargs = mock_client.images.create.call_args.kwargs
        assert call_kwargs["model"] == "wanx-v1"
        assert call_kwargs["negative_prompt"] == "people,cars"
        assert call_kwargs["seed"] == 12345
        assert call_kwargs["prompt_extend"] is True
        assert call_kwargs["watermark"] is False

    def test_generate_open_without_output_fails(self) -> None:
        """Generate with --open but no -o fails."""
        from r9s.cli_tools.image_cli import handle_image_generate

        args = argparse.Namespace(
            prompt="A cat",
            output=None,
            model=None,
            size=None,
            quality=None,
            n=1,
            style=None,
            negative_prompt=None,
            seed=None,
            prompt_extend=None,
            watermark=None,
            format=None,
            json=False,
            open=True,  # --open without -o
            background=None,
            output_format=None,
        )

        with pytest.raises(SystemExit):
            handle_image_generate(args)

    def test_generate_passes_new_options(self) -> None:
        """Generate passes background and output_format to API."""
        from r9s.cli_tools.image_cli import handle_image_generate

        args = argparse.Namespace(
            prompt="A logo",
            output=None,
            model="gpt-image-1",
            size=None,
            quality=None,
            n=1,
            style=None,
            negative_prompt=None,
            seed=None,
            prompt_extend=None,
            watermark=None,
            format=None,
            json=False,
            open=False,
            background="transparent",
            output_format="png",
        )

        mock_image = MagicMock()
        mock_image.url = "https://example.com/image.png"
        mock_image.b64_json = None
        mock_image.revised_prompt = None

        mock_response = MagicMock()
        mock_response.data = [mock_image]
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.images.create.return_value = mock_response

        with patch("r9s.cli_tools.image_cli.get_client", return_value=mock_client):
            with patch("r9s.cli_tools.image_cli.LoadingSpinner"):
                handle_image_generate(args)

        call_kwargs = mock_client.images.create.call_args.kwargs
        assert call_kwargs["background"] == "transparent"
        assert call_kwargs["output_format"] == "png"


class TestImageEditHandler:
    """Tests for handle_image_edit function."""

    def test_edit_file_not_found(self, tmp_path: Path) -> None:
        """Edit with nonexistent image file fails."""
        from r9s.cli_tools.image_cli import handle_image_edit

        args = argparse.Namespace(
            image=str(tmp_path / "nonexistent.png"),
            prompt="Add a hat",
            output=None,
            mask=None,
            model=None,
            size=None,
            n=1,
            format=None,
            json=False,
        )

        with pytest.raises(SystemExit):
            handle_image_edit(args)

    def test_edit_success(self, tmp_path: Path, capsys: Any) -> None:
        """Edit successfully returns URL."""
        from r9s.cli_tools.image_cli import handle_image_edit

        # Create test image file
        test_image = tmp_path / "input.png"
        test_image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        args = argparse.Namespace(
            image=str(test_image),
            prompt="Add a hat",
            output=None,
            mask=None,
            model=None,
            size=None,
            n=1,
            format=None,
            json=False,
        )

        mock_image = MagicMock()
        mock_image.url = "https://example.com/edited.png"
        mock_image.b64_json = None

        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.edit.return_value = mock_response

        with patch("r9s.cli_tools.image_cli.get_client", return_value=mock_client):
            with patch("r9s.cli_tools.image_cli.LoadingSpinner"):
                handle_image_edit(args)

        captured = capsys.readouterr()
        assert "https://example.com/edited.png" in captured.out

    def test_edit_with_mask(self, tmp_path: Path) -> None:
        """Edit includes mask in API call."""
        from r9s.cli_tools.image_cli import handle_image_edit

        # Create test files
        test_image = tmp_path / "input.png"
        test_image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        test_mask = tmp_path / "mask.png"
        test_mask.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 30)

        args = argparse.Namespace(
            image=str(test_image),
            prompt="Replace background",
            output=None,
            mask=str(test_mask),
            model=None,
            size=None,
            n=1,
            format=None,
            json=False,
        )

        mock_image = MagicMock()
        mock_image.url = "https://example.com/edited.png"
        mock_image.b64_json = None

        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.edit.return_value = mock_response

        with patch("r9s.cli_tools.image_cli.get_client", return_value=mock_client):
            with patch("r9s.cli_tools.image_cli.LoadingSpinner"):
                handle_image_edit(args)

        # Verify mask was included
        call_kwargs = mock_client.images.edit.call_args.kwargs
        assert "mask" in call_kwargs
        assert call_kwargs["mask"]["file_name"] == "mask.png"
