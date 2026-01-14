"""CLI handlers for image generation and editing."""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from r9s.cli_tools.config import get_api_key, resolve_base_url, resolve_image_model, resolve_model
from r9s.cli_tools.ui.spinner import LoadingSpinner
from r9s.cli_tools.ui.terminal import error, info, success, warning


def get_client():
    """Create and return an R9S client."""
    from r9s import R9S

    api_key = get_api_key(None)
    if not api_key:
        error("R9S_API_KEY is not set. Use --api-key or set the environment variable.")
        raise SystemExit(1)

    base_url = resolve_base_url(None)

    return R9S(api_key=api_key, server_url=base_url)


def read_image_file(path: Path) -> bytes:
    """Read an image file and return its contents."""
    if not path.exists():
        error(f"Image file not found: {path}")
        raise SystemExit(1)
    return path.read_bytes()


def save_image(data: bytes, output_path: Path) -> None:
    """Save image data to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    success(f"Saved: {output_path}")


def download_image(url: str) -> bytes:
    """Download image from URL."""
    import urllib.request

    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def generate_output_filename(base_dir: Path, index: int, total: int, ext: str = "png") -> Path:
    """Generate output filename for multiple images."""
    if total == 1:
        return base_dir / f"image.{ext}"
    return base_dir / f"image_{index + 1}.{ext}"


def open_file(path: Path) -> None:
    """Open a file with the system's default application."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(path)], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(path)], check=True)
        elif system == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            warning(f"Don't know how to open files on {system}")
    except Exception as e:
        warning(f"Could not open file: {e}")


def open_files(paths: List[Path]) -> None:
    """Open multiple files with the system's default application."""
    for path in paths:
        open_file(path)


def handle_image_generate(args: argparse.Namespace) -> None:
    """Handle image generation command."""
    # Get prompt from args or stdin
    prompt = args.prompt
    if not prompt:
        if sys.stdin.isatty():
            error("Prompt is required. Provide as argument or pipe via stdin.")
            raise SystemExit(1)
        prompt = sys.stdin.read().strip()
        if not prompt:
            error("Empty prompt received from stdin.")
            raise SystemExit(1)

    # Validate n and output combination
    n = args.n or 1
    output = Path(args.output) if args.output else None
    should_open = getattr(args, "open", False)
    reference_paths = getattr(args, "reference", None) or []

    # --open requires -o (need files to open)
    if should_open and not output:
        error("--open requires --output to save files first.")
        raise SystemExit(1)

    if n > 1 and output and not output.is_dir() and output.exists():
        error("When generating multiple images (-n > 1), --output must be a directory.")
        raise SystemExit(1)

    # Determine output file extension from output_format
    output_ext = getattr(args, "output_format", None) or "png"

    client = get_client()
    model = resolve_image_model(args.model)

    # If reference images are provided, use edit endpoint for style transfer
    if reference_paths:
        # Read reference images
        reference_images = []
        for i, ref_path in enumerate(reference_paths):
            ref_file = Path(ref_path)
            if not ref_file.exists():
                error(f"Reference image not found: {ref_path}")
                raise SystemExit(1)
            ref_data = ref_file.read_bytes()
            reference_images.append({
                "file_name": ref_file.name,
                "content": ref_data,
                "content_type": _get_image_mime_type(ref_file),
            })
            info(f"Reference {i+1}: {ref_file.name} ({len(ref_data)} bytes)")

        # Build edit kwargs - always pass as list for multiple images
        edit_kwargs: dict = {
            "image": reference_images,
            "prompt": prompt,
            "model": model,
            "n": n,
        }

        if args.size:
            edit_kwargs["size"] = args.size
        if getattr(args, "background", None):
            edit_kwargs["background"] = args.background
        if getattr(args, "output_format", None):
            edit_kwargs["output_format"] = args.output_format

        if getattr(args, "verbose", False):
            info(f"Endpoint: POST /v1/images/edits")
            info(f"Model: {model}")
            info(f"Images: {len(reference_images)}")
            info(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        with LoadingSpinner("Generating with reference"):
            try:
                result = client.images.edit(**edit_kwargs)
            except Exception as e:
                error(f"API error: {e}")
                raise SystemExit(1)
    else:
        # Build standard generation kwargs
        kwargs = {
            "prompt": prompt,
            "model": model,
            "n": n,
        }

        # Only include response_format if explicitly specified (not all models support it)
        # GPT image models don't support response_format at all
        if args.format and not _is_gpt_image_model(model):
            kwargs["response_format"] = "b64_json" if args.format == "b64" else "url"

        if args.size:
            kwargs["size"] = args.size
        if args.quality:
            kwargs["quality"] = args.quality
        if args.style:
            kwargs["style"] = args.style
        if args.negative_prompt:
            kwargs["negative_prompt"] = args.negative_prompt
        if args.seed is not None:
            kwargs["seed"] = args.seed
        if args.prompt_extend is not None:
            kwargs["prompt_extend"] = args.prompt_extend
        if args.watermark is not None:
            kwargs["watermark"] = args.watermark
        # New options
        if getattr(args, "background", None):
            kwargs["background"] = args.background
        if getattr(args, "output_format", None):
            kwargs["output_format"] = args.output_format

        if getattr(args, "verbose", False):
            info(f"Endpoint: POST /v1/images/generations")
            info(f"Model: {model}")
            info(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        # Make API call
        with LoadingSpinner("Generating image"):
            try:
                result = client.images.create(**kwargs)
            except Exception as e:
                error(f"API error: {e}")
                raise SystemExit(1)

    # Handle output
    if args.json:
        # Output full JSON response
        print(json.dumps(result.model_dump(), indent=2, default=str))
        return

    saved_files: List[Path] = []

    for i, image in enumerate(result.data):
        if output:
            # Save to file
            if output.suffix:
                # Single file specified
                out_path = output if n == 1 else output.parent / f"{output.stem}_{i + 1}{output.suffix}"
            else:
                # Directory specified
                out_path = generate_output_filename(output, i, len(result.data), output_ext)

            if image.b64_json:
                image_data = base64.b64decode(image.b64_json)
                save_image(image_data, out_path)
                saved_files.append(out_path)
            elif image.url:
                info(f"Downloading image {i + 1}...")
                image_data = download_image(image.url)
                save_image(image_data, out_path)
                saved_files.append(out_path)
        else:
            # Print URL
            if image.url:
                print(image.url)
            elif image.b64_json:
                warning(f"Image {i + 1}: [base64 data, use -o to save]")

        # Show revised prompt if available
        if image.revised_prompt and not args.json:
            info(f"Revised prompt: {image.revised_prompt}")

    # Show usage if available
    if result.usage and not args.json:
        usage_parts = []
        if result.usage.prompt_tokens:
            usage_parts.append(f"prompt_tokens={result.usage.prompt_tokens}")
        if result.usage.image_tokens:
            usage_parts.append(f"image_tokens={result.usage.image_tokens}")
        if usage_parts:
            info(f"Usage: {', '.join(usage_parts)}")

    # Open files if requested
    if should_open and saved_files:
        open_files(saved_files)


def handle_image_edit(args: argparse.Namespace) -> None:
    """Handle image editing command."""
    # Read source image
    image_path = Path(args.image)
    image_data = read_image_file(image_path)

    # Get prompt
    prompt = args.prompt
    if not prompt:
        error("Prompt is required for image editing.")
        raise SystemExit(1)

    # Read mask if provided
    mask_data = None
    if args.mask:
        mask_path = Path(args.mask)
        mask_data = read_image_file(mask_path)

    # Validate n and output combination
    n = args.n or 1
    output = Path(args.output) if args.output else None
    should_open = getattr(args, "open", False)

    # --open requires -o (need files to open)
    if should_open and not output:
        error("--open requires --output to save files first.")
        raise SystemExit(1)

    if n > 1 and output and not output.is_dir() and output.exists():
        error("When generating multiple images (-n > 1), --output must be a directory.")
        raise SystemExit(1)

    # Determine output file extension from output_format
    output_ext = getattr(args, "output_format", None) or "png"

    # Build request kwargs
    kwargs = {
        "image": {"file_name": image_path.name, "content": image_data},
        "prompt": prompt,
        "model": resolve_image_model(args.model),
        "n": n,
    }

    # Only include response_format if explicitly specified (not all models support it)
    if args.format:
        kwargs["response_format"] = "b64_json" if args.format == "b64" else "url"

    if args.size:
        kwargs["size"] = args.size
    if mask_data:
        mask_path = Path(args.mask)
        kwargs["mask"] = {"file_name": mask_path.name, "content": mask_data}
    # New options
    if getattr(args, "background", None):
        kwargs["background"] = args.background
    if getattr(args, "output_format", None):
        kwargs["output_format"] = args.output_format

    # Make API call
    client = get_client()
    model = kwargs["model"]

    if getattr(args, "verbose", False):
        info(f"Endpoint: POST /v1/images/edits")
        info(f"Model: {model}")
        info(f"Image: {image_path.name}")
        if mask_data:
            info(f"Mask: {args.mask}")
        info(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

    with LoadingSpinner("Editing image"):
        try:
            result = client.images.edit(**kwargs)
        except Exception as e:
            error(f"API error: {e}")
            raise SystemExit(1)

    # Handle output
    if args.json:
        print(json.dumps(result.model_dump(), indent=2, default=str))
        return

    saved_files: List[Path] = []

    for i, image in enumerate(result.data):
        if output:
            # Save to file
            if output.suffix:
                out_path = output if n == 1 else output.parent / f"{output.stem}_{i + 1}{output.suffix}"
            else:
                out_path = generate_output_filename(output, i, len(result.data), output_ext)

            if image.b64_json:
                image_data = base64.b64decode(image.b64_json)
                save_image(image_data, out_path)
                saved_files.append(out_path)
            elif image.url:
                info(f"Downloading image {i + 1}...")
                image_data = download_image(image.url)
                save_image(image_data, out_path)
                saved_files.append(out_path)
        else:
            if image.url:
                print(image.url)
            elif image.b64_json:
                warning(f"Image {i + 1}: [base64 data, use -o to save]")

    # Open files if requested
    if should_open and saved_files:
        open_files(saved_files)


def _is_gpt5_model(model: str) -> bool:
    """Check if model is a GPT-5 variant that requires special parameters."""
    return model.lower().startswith("gpt-5")


def _is_gpt_image_model(model: str) -> bool:
    """Check if model is a GPT image model that doesn't support response_format."""
    return model.lower().startswith("gpt-image")


def _get_image_mime_type(path: Path) -> str:
    """Detect image MIME type from file extension."""
    ext = path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_types.get(ext, "image/png")


def handle_image_describe(args: argparse.Namespace) -> None:
    """Handle image describe command using vision."""
    # Read source image
    image_path = Path(args.image)
    image_data = read_image_file(image_path)

    # Get prompt (default to "Describe this image.")
    prompt = args.prompt or "Describe this image in detail."
    if getattr(args, "detailed", False):
        prompt = (
            "Describe this image in comprehensive detail. Include: "
            "the main subject, colors, composition, mood, any text visible, "
            "background elements, and any notable details."
        )

    # Build data URL
    mime_type = _get_image_mime_type(image_path)
    b64 = base64.b64encode(image_data).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    # Build message with image
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url, "detail": "auto"}},
            ],
        }
    ]

    # Make API call
    client = get_client()
    model = resolve_model(args.model)
    max_tokens_value = getattr(args, "max_tokens", None) or 1024

    # Build kwargs - GPT-5 models require max_completion_tokens instead of max_tokens
    chat_kwargs: dict = {
        "model": model,
        "messages": messages,
    }
    if _is_gpt5_model(model):
        chat_kwargs["max_completion_tokens"] = max_tokens_value
    else:
        chat_kwargs["max_tokens"] = max_tokens_value

    with LoadingSpinner("Analyzing image"):
        try:
            result = client.chat.create(**chat_kwargs)
        except Exception as e:
            error(f"API error: {e}")
            raise SystemExit(1)

    # Output result
    if args.json:
        print(json.dumps(result.model_dump(), indent=2, default=str))
    else:
        content = result.choices[0].message.content
        print(content)
