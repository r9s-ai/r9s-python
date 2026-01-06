"""CLI handlers for audio: TTS (speech), ASR (transcribe), and translation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from r9s import R9S, errors
from r9s.cli_tools.config import get_api_key, resolve_base_url
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.cli_tools.ui.spinner import LoadingSpinner
from r9s.cli_tools.ui.terminal import error, info, success


def _get_client(api_key: Optional[str], base_url: Optional[str]) -> R9S:
    """Create and return an R9S client."""
    key = get_api_key(api_key)
    if not key:
        error("R9S_API_KEY is not set. Use --api-key or set the environment variable.")
        raise SystemExit(1)
    url = resolve_base_url(base_url)
    return R9S(api_key=key, server_url=url)


def handle_audio_speech(args: argparse.Namespace) -> None:
    """Handle text-to-speech command."""
    # Get text from args or stdin
    text = args.text
    if not text:
        if sys.stdin.isatty():
            error("Text is required. Provide as argument or pipe via stdin.")
            raise SystemExit(1)
        text = sys.stdin.read().strip()
        if not text:
            error("Empty text received from stdin.")
            raise SystemExit(1)

    # Determine output path
    output = Path(args.output) if args.output else None
    if not output:
        error("Output file is required. Use -o/--output to specify.")
        raise SystemExit(1)

    # Build request kwargs
    kwargs = {
        "input": text,
        "model": args.model or "tts-1",
        "voice": args.voice or "alloy",
    }

    if args.speed:
        kwargs["speed"] = args.speed
    if args.format:
        kwargs["response_format"] = args.format

    # Make API call
    client = _get_client(args.api_key, args.base_url)
    with LoadingSpinner("Generating speech"):
        try:
            response = client.audio.speech(**kwargs)
        except errors.AuthenticationError as exc:
            error(f"Authentication failed: {exc}")
            raise SystemExit(1)
        except errors.R9SError as exc:
            error(f"API error: {exc}")
            raise SystemExit(1)

    # Save audio to file
    output.parent.mkdir(parents=True, exist_ok=True)
    audio_data = response.read()
    output.write_bytes(audio_data)
    success(f"Saved: {output}")

    # Show file size
    size_kb = len(audio_data) / 1024
    info(f"Size: {size_kb:.1f} KB")


def handle_audio_transcribe(args: argparse.Namespace) -> None:
    """Handle speech-to-text (transcription) command."""
    # Read audio file
    audio_path = Path(args.audio)
    if not audio_path.exists():
        error(f"Audio file not found: {audio_path}")
        raise SystemExit(1)

    audio_data = audio_path.read_bytes()

    # Build request kwargs
    kwargs = {
        "file": {"file_name": audio_path.name, "content": audio_data},
        "model": args.model or "whisper-1",
    }

    if args.language:
        kwargs["language"] = args.language
    if args.prompt:
        kwargs["prompt"] = args.prompt
    if args.format:
        kwargs["response_format"] = args.format

    # Make API call
    client = _get_client(args.api_key, args.base_url)
    with LoadingSpinner("Transcribing audio"):
        try:
            response = client.audio.transcribe(**kwargs)
        except errors.AuthenticationError as exc:
            error(f"Authentication failed: {exc}")
            raise SystemExit(1)
        except errors.R9SError as exc:
            error(f"API error: {exc}")
            raise SystemExit(1)

    # Extract text from response
    if isinstance(response, str):
        text = response
    elif hasattr(response, "text"):
        text = response.text
    else:
        text = str(response)

    # Output result
    output = Path(args.output) if args.output else None
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        success(f"Saved: {output}")
    else:
        print(text)


def handle_audio_translate(args: argparse.Namespace) -> None:
    """Handle speech translation (to English) command."""
    # Read audio file
    audio_path = Path(args.audio)
    if not audio_path.exists():
        error(f"Audio file not found: {audio_path}")
        raise SystemExit(1)

    audio_data = audio_path.read_bytes()

    # Build request kwargs
    kwargs = {
        "file": {"file_name": audio_path.name, "content": audio_data},
        "model": args.model or "whisper-1",
    }

    if args.prompt:
        kwargs["prompt"] = args.prompt
    if args.format:
        kwargs["response_format"] = args.format

    # Make API call
    client = _get_client(args.api_key, args.base_url)
    with LoadingSpinner("Translating audio to English"):
        try:
            response = client.audio.translate(**kwargs)
        except errors.AuthenticationError as exc:
            error(f"Authentication failed: {exc}")
            raise SystemExit(1)
        except errors.R9SError as exc:
            error(f"API error: {exc}")
            raise SystemExit(1)

    # Extract text from response
    if isinstance(response, str):
        text = response
    elif hasattr(response, "text"):
        text = response.text
    else:
        text = str(response)

    # Output result
    output = Path(args.output) if args.output else None
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        success(f"Saved: {output}")
    else:
        print(text)
