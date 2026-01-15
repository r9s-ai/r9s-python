"""
Code Q&A CLI - Ask questions about indexed codebases using RAG.

Usage:
  r9s code ask edgefn/next-router "How does routing work?"
  r9s code ask edgefn/next-router  # Interactive chat mode
  echo "How does auth work?" | r9s code ask edgefn/next-router
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from r9s.cli_tools.config import get_api_key, resolve_base_url, resolve_model
from r9s.cli_tools.i18n import resolve_lang
from r9s.cli_tools.ui.terminal import FG_CYAN, error, header, info
from r9s.cli_tools.ui.spinner import Spinner
from r9s.cli_tools.ui.rich_output import is_rich_available, is_rich_enabled, print_markdown
from r9s.cli_tools.ui.chat_prompt import chat_prompt, create_chat_session


DEFAULT_CODE_SERVICE_URL = "http://44.252.28.1:8123/code-review"


def _is_gpt5_model(model: str) -> bool:
    """Check if model is a GPT-5 variant that doesn't support sampling parameters."""
    return model.lower().startswith("gpt-5")


def _get_code_service_url() -> str:
    """Get code service URL from environment or default."""
    return os.getenv("R9S_CODE_SERVICE_URL", DEFAULT_CODE_SERVICE_URL)


def _fetch_context(
    service_url: str,
    repo: str,
    query: str,
    max_chunks: int = 5,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """Fetch RAG context from the code-review service."""
    url = f"{service_url.rstrip('/')}/api/context"
    payload = json.dumps({
        "repo": repo,
        "query": query,
        "maxChunks": max_chunks,
        "threshold": threshold,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Code service error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to connect to code service: {exc}") from exc


def _build_code_prompt(query: str, context: Dict[str, Any]) -> str:
    """Build a prompt with code context for the LLM."""
    chunks = context.get("chunks", [])
    repo = context.get("repo", "unknown")

    prompt_parts = [
        f"# Codebase Q&A: {repo}\n",
        f"## Question\n{query}\n",
        "## Relevant Code Context\n",
    ]

    for chunk in chunks:
        file_path = chunk.get("file", "unknown")
        line_start = chunk.get("lineStart", 0)
        line_end = chunk.get("lineEnd", 0)
        content = chunk.get("content", "")
        name = chunk.get("name", "")
        relevance = chunk.get("relevance", 0)

        header_line = f"### {file_path}:{line_start}-{line_end}"
        if name:
            header_line += f" ({name})"
        header_line += f" [relevance: {relevance:.2f}]"

        prompt_parts.append(f"{header_line}\n```\n{content}\n```\n")

    prompt_parts.append(
        "\n## Instructions\n"
        "Answer the question based on the code context above. "
        "Reference specific files and line numbers when relevant. "
        "If the context doesn't contain enough information, say so.\n"
    )

    return "\n".join(prompt_parts)


def _stream_chat(
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    use_rich: bool = False,
) -> str:
    """Stream chat completion using direct HTTP (unbuffered).

    Returns the full response text for optional rich rendering.
    """
    import http.client
    from urllib.parse import urlparse

    parsed = urlparse(base_url.rstrip('/'))
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    path = f"{parsed.path}/chat/completions"

    # Build request payload - gpt-5 models don't support temperature
    request_body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if not _is_gpt5_model(model):
        request_body["temperature"] = 0.3

    payload = json.dumps(request_body)

    if parsed.scheme == 'https':
        import ssl
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(host, port, context=ctx, timeout=120)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=120)

    collected: List[str] = []
    try:
        conn.request(
            "POST",
            path,
            body=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Accept": "text/event-stream",
            },
        )
        resp = conn.getresponse()

        if resp.status >= 400:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                err_data = json.loads(body)
                reason = err_data.get("reason") or err_data.get("error", {}).get("message", body)
            except json.JSONDecodeError:
                reason = body
            raise RuntimeError(f"API error {resp.status}: {reason}")

        # Use socket file for unbuffered line reading
        sock_file = resp.fp
        while True:
            line = sock_file.readline()
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                    if "error" in event:
                        raise RuntimeError(f"API error: {event['error']}")
                    if event.get("choices"):
                        delta = event["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            collected.append(content)
                            if not use_rich:
                                print(content, end="", flush=True)
                except json.JSONDecodeError:
                    continue

        if not use_rich:
            print()
        return "".join(collected)
    finally:
        conn.close()


def _print_references(chunks: List[Dict[str, Any]], max_refs: int = 3) -> None:
    """Print code references."""
    info("References:")
    for chunk in chunks[:max_refs]:
        file_path = chunk.get("file", "")
        line_start = chunk.get("lineStart", 0)
        line_end = chunk.get("lineEnd", 0)
        relevance = chunk.get("relevance", 0)
        print(f"  - {file_path}:{line_start}-{line_end} (relevance: {relevance:.2f})")


def _ask_single_question(
    query: str,
    repo: str,
    service_url: str,
    max_chunks: int,
    base_url: str,
    api_key: str,
    model: str,
    use_rich: bool,
    history: List[Dict[str, str]],
) -> Optional[str]:
    """Ask a single question with RAG context. Returns the answer text."""
    # Fetch context
    spinner = Spinner("Retrieving code context...")
    if sys.stdout.isatty():
        spinner.start()

    try:
        context = _fetch_context(
            service_url=service_url,
            repo=repo,
            query=query,
            max_chunks=max_chunks,
        )
    except RuntimeError as exc:
        spinner.stop_and_clear()
        error(str(exc))
        return None
    finally:
        spinner.stop_and_clear()

    chunks = context.get("chunks", [])
    retrieval_ms = context.get("retrievalTimeMs", 0)

    if not chunks:
        error(f"No relevant code found for '{query}'. Make sure the repository is indexed.")
        return None

    info(f"Found {len(chunks)} code chunks in {retrieval_ms}ms")

    # Build messages with history
    system_prompt = (
        "You are a helpful assistant that answers questions about codebases. "
        "Answer based on the provided code context. "
        "Be concise but thorough. Use code blocks when showing examples."
    )

    # Build messages: system + history + current question with code context
    user_prompt = _build_code_prompt(query, context)
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    try:
        answer_text = _stream_chat(base_url, api_key, model, messages, use_rich=use_rich)
        if use_rich and answer_text:
            print_markdown(answer_text)

        # Print references
        print()
        _print_references(chunks)

        return answer_text
    except RuntimeError as exc:
        error(str(exc))
        return None


def handle_code_ask(args: argparse.Namespace) -> None:
    """Handle 'r9s code ask' command - single question or interactive chat."""
    lang = resolve_lang(getattr(args, "lang", None))

    # Get API credentials
    api_key = get_api_key(args.api_key)
    if not api_key:
        raise SystemExit("R9S_API_KEY not set. Set it or use --api-key.")

    base_url = resolve_base_url(args.base_url)
    model = resolve_model(args.model)
    if not model:
        model = os.getenv("R9S_MODEL", "GLM-4.7")

    # Get repo
    repo = args.repo
    if not repo:
        raise SystemExit("Repository is required (e.g., edgefn/next-router)")

    # Get service URL and settings
    service_url = getattr(args, "service_url", None) or _get_code_service_url()
    max_chunks = getattr(args, "max_chunks", 5) or 5

    # Check rich rendering
    use_rich = getattr(args, "rich", False) or is_rich_enabled()
    if use_rich and not is_rich_available():
        info("Rich rendering requested but not available. Install with: pip install r9s[rich]")
        use_rich = False

    # Get query from args or stdin
    query_parts = getattr(args, "query", []) or []
    if query_parts:
        # Single question mode
        query = " ".join(query_parts)
        history: List[Dict[str, str]] = []
        answer = _ask_single_question(
            query, repo, service_url, max_chunks,
            base_url, api_key, model, use_rich, history
        )
        if answer is None:
            raise SystemExit(1)
        return

    elif not sys.stdin.isatty():
        # Piped input - single question mode
        query = sys.stdin.read().strip()
        if not query:
            raise SystemExit("Question cannot be empty.")
        history = []
        answer = _ask_single_question(
            query, repo, service_url, max_chunks,
            base_url, api_key, model, use_rich, history
        )
        if answer is None:
            raise SystemExit(1)
        return

    # Interactive chat mode
    header(f"Code Q&A: {repo}")
    info(f"Model: {model}")
    info(f"Service: {service_url}")
    info("Commands: /exit, /clear, /help")
    print()

    history: List[Dict[str, str]] = []
    prompt_session = create_chat_session()

    while True:
        try:
            user_text = chat_prompt(prompt_session, "You: ", color=FG_CYAN)
        except EOFError:
            print()
            return

        if not user_text:
            continue

        # Handle commands
        if user_text.lower() in ("exit", "quit", "bye", "/exit"):
            return
        if user_text == "/clear":
            history.clear()
            info("Conversation history cleared.")
            continue
        if user_text == "/help":
            info("Commands:")
            print("  /exit  - Exit the chat")
            print("  /clear - Clear conversation history")
            print("  /help  - Show this help")
            continue

        # Ask the question
        answer = _ask_single_question(
            user_text, repo, service_url, max_chunks,
            base_url, api_key, model, use_rich, history
        )

        if answer:
            # Add to history (simplified - just the question and answer, not full context)
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": answer})

        print()  # Blank line between turns
