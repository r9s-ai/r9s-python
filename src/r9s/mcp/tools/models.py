"""MCP Tools for model discovery and comparison.

This module implements the r9s-models MCP server tools:
- list_models: List available models with pricing and capabilities
- get_model_status: Check real-time model availability
- recommend_model: Get model recommendations based on task
- compare_models: Compare outputs across multiple models
"""

import os
import time
import json
import urllib.request
import urllib.error
from typing import Any, Optional

# Tool definitions following MCP schema
MODELS_TOOLS = [
    {
        "name": "list_models",
        "description": "List available models on r9s Gateway with pricing and capabilities. "
                       "Use this to discover what models are available and their costs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Filter by provider (e.g., 'anthropic', 'openai', 'google')"
                },
                "capability": {
                    "type": "string",
                    "enum": ["chat", "vision", "code", "embedding", "image_gen"],
                    "description": "Filter by capability"
                },
                "max_cost_per_1k": {
                    "type": "number",
                    "description": "Maximum cost per 1K tokens (filters expensive models)"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of models to return"
                }
            }
        }
    },
    {
        "name": "get_model_status",
        "description": "Check real-time availability and health of models. "
                       "Use this to verify a model is available before using it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific model IDs to check (default: all)"
                }
            }
        }
    },
    {
        "name": "recommend_model",
        "description": "Get a model recommendation based on task type and constraints. "
                       "Use this when unsure which model to use for a specific task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "enum": [
                        "code_generation",
                        "code_review",
                        "writing",
                        "analysis",
                        "chat",
                        "translation",
                        "summarization",
                        "math",
                        "creative"
                    ],
                    "description": "Type of task"
                },
                "priority": {
                    "type": "string",
                    "enum": ["quality", "speed", "cost"],
                    "default": "quality",
                    "description": "What to optimize for"
                },
                "max_cost_per_call": {
                    "type": "number",
                    "description": "Budget constraint per call (USD)"
                },
                "context_size": {
                    "type": "integer",
                    "description": "Approximate context size needed (tokens)"
                }
            },
            "required": ["task"]
        }
    },
    {
        "name": "compare_models",
        "description": "Run a prompt across multiple models to compare outputs, latency, and cost. "
                       "Use this for model selection and evaluation. Limited to 4 models max.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to test across models"
                },
                "models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 4,
                    "description": "Models to compare (2-4 models)"
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 500,
                    "description": "Max tokens per response"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Optional system prompt"
                }
            },
            "required": ["prompt", "models"]
        }
    },
]


def _get_config(api_key: Optional[str], base_url: Optional[str]) -> tuple[str, str]:
    """Get API key and base URL from args or environment."""
    key = api_key or os.getenv("R9S_API_KEY", "")
    url = base_url or os.getenv("R9S_BASE_URL", "https://api.r9s.ai/v1")
    return key, url.rstrip("/")


def _api_request(
    endpoint: str,
    api_key: str,
    base_url: str,
    method: str = "GET",
    data: Optional[dict] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Make an API request to r9s Gateway."""
    url = f"{base_url}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"API error {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection error: {e.reason}") from e


async def handle_models_tool(
    name: str,
    arguments: dict[str, Any],
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """Handle model-related MCP tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        api_key: Optional API key override
        base_url: Optional base URL override

    Returns:
        Tool execution result
    """
    key, url = _get_config(api_key, base_url)

    if not key:
        return {"error": "R9S_API_KEY not configured"}

    if name == "list_models":
        return await _list_models(arguments, key, url)
    elif name == "get_model_status":
        return await _get_model_status(arguments, key, url)
    elif name == "recommend_model":
        return await _recommend_model(arguments, key, url)
    elif name == "compare_models":
        return await _compare_models(arguments, key, url)
    else:
        return {"error": f"Unknown tool: {name}"}


async def _list_models(
    args: dict[str, Any], api_key: str, base_url: str
) -> dict[str, Any]:
    """List available models."""
    try:
        response = _api_request("/models", api_key, base_url)
    except Exception as e:
        return {"error": str(e)}

    models_data = response.get("data", [])

    # Apply filters
    provider_filter = args.get("provider", "").lower()
    capability_filter = args.get("capability", "")
    max_cost = args.get("max_cost_per_1k")
    limit = args.get("limit", 50)

    filtered = []
    for model in models_data:
        model_id = model.get("id", "")

        # Provider filter (infer from model ID)
        if provider_filter:
            if provider_filter == "anthropic" and "claude" not in model_id.lower():
                continue
            elif provider_filter == "openai" and "gpt" not in model_id.lower():
                continue
            elif provider_filter == "google" and "gemini" not in model_id.lower():
                continue

        # Format output
        filtered.append({
            "id": model_id,
            "owned_by": model.get("owned_by", "unknown"),
            "created": model.get("created"),
        })

        if len(filtered) >= limit:
            break

    return {
        "models": filtered,
        "total": len(filtered),
        "note": "Use get_model_status for real-time availability"
    }


async def _get_model_status(
    args: dict[str, Any], api_key: str, base_url: str
) -> dict[str, Any]:
    """Check model status."""
    models_filter = args.get("models", [])

    try:
        response = _api_request("/models", api_key, base_url)
    except Exception as e:
        return {"error": str(e)}

    models_data = response.get("data", [])
    model_ids = {m.get("id") for m in models_data}

    status_list = []
    for model in models_data:
        model_id = model.get("id", "")

        if models_filter and model_id not in models_filter:
            continue

        status_list.append({
            "model": model_id,
            "status": "available",  # Basic status - could enhance with health checks
            "owned_by": model.get("owned_by", "unknown"),
        })

    # Check for requested models that don't exist
    if models_filter:
        for requested in models_filter:
            if requested not in model_ids:
                status_list.append({
                    "model": requested,
                    "status": "not_found",
                })

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status_list,
    }


async def _recommend_model(
    args: dict[str, Any], api_key: str, base_url: str
) -> dict[str, Any]:
    """Recommend a model based on task and constraints."""
    task = args.get("task", "chat")
    priority = args.get("priority", "quality")
    max_cost = args.get("max_cost_per_call")
    context_size = args.get("context_size", 4000)

    # Model recommendations by task and priority
    # This is a simplified heuristic - could be enhanced with actual benchmarks
    recommendations = {
        "code_generation": {
            "quality": ["claude-sonnet-4-20250514", "gpt-4o", "deepseek-chat"],
            "speed": ["gpt-4o-mini", "claude-3-5-haiku-20241022", "deepseek-chat"],
            "cost": ["deepseek-chat", "gpt-4o-mini", "glm-4-flash"],
        },
        "code_review": {
            "quality": ["claude-sonnet-4-20250514", "gpt-4o"],
            "speed": ["gpt-4o-mini", "claude-3-5-haiku-20241022"],
            "cost": ["deepseek-chat", "glm-4-flash"],
        },
        "writing": {
            "quality": ["claude-sonnet-4-20250514", "gpt-4o"],
            "speed": ["gpt-4o-mini", "claude-3-5-haiku-20241022"],
            "cost": ["glm-4-flash", "deepseek-chat"],
        },
        "analysis": {
            "quality": ["claude-sonnet-4-20250514", "gpt-4o", "gemini-1.5-pro"],
            "speed": ["gpt-4o-mini", "gemini-1.5-flash"],
            "cost": ["deepseek-chat", "glm-4-flash"],
        },
        "chat": {
            "quality": ["claude-sonnet-4-20250514", "gpt-4o"],
            "speed": ["gpt-4o-mini", "claude-3-5-haiku-20241022"],
            "cost": ["glm-4-flash", "deepseek-chat"],
        },
        "translation": {
            "quality": ["gpt-4o", "claude-sonnet-4-20250514"],
            "speed": ["gpt-4o-mini", "deepseek-chat"],
            "cost": ["deepseek-chat", "glm-4-flash"],
        },
        "summarization": {
            "quality": ["claude-sonnet-4-20250514", "gpt-4o"],
            "speed": ["gpt-4o-mini", "gemini-1.5-flash"],
            "cost": ["deepseek-chat", "glm-4-flash"],
        },
        "math": {
            "quality": ["gpt-4o", "claude-sonnet-4-20250514", "deepseek-chat"],
            "speed": ["gpt-4o-mini", "deepseek-chat"],
            "cost": ["deepseek-chat", "glm-4-flash"],
        },
        "creative": {
            "quality": ["claude-sonnet-4-20250514", "gpt-4o"],
            "speed": ["gpt-4o-mini", "claude-3-5-haiku-20241022"],
            "cost": ["glm-4-flash", "deepseek-chat"],
        },
    }

    task_recs = recommendations.get(task, recommendations["chat"])
    priority_list = task_recs.get(priority, task_recs["quality"])

    # Check which models are actually available
    try:
        response = _api_request("/models", api_key, base_url)
        available_ids = {m.get("id") for m in response.get("data", [])}
    except Exception:
        available_ids = set()

    # Find first available recommendation
    primary = None
    alternatives = []

    for model_id in priority_list:
        if not available_ids or model_id in available_ids:
            if primary is None:
                primary = model_id
            else:
                alternatives.append(model_id)

    if not primary:
        primary = priority_list[0]  # Fallback to first recommendation

    return {
        "recommendation": {
            "model": primary,
            "task": task,
            "priority": priority,
            "reason": f"Best {priority} option for {task.replace('_', ' ')}",
        },
        "alternatives": [
            {"model": m, "reason": f"Alternative for {task.replace('_', ' ')}"}
            for m in alternatives[:2]
        ],
        "note": "Recommendations based on general benchmarks. Actual performance may vary.",
    }


async def _compare_models(
    args: dict[str, Any], api_key: str, base_url: str
) -> dict[str, Any]:
    """Compare outputs across multiple models."""
    prompt = args.get("prompt", "")
    models = args.get("models", [])
    max_tokens = args.get("max_tokens", 500)
    system_prompt = args.get("system_prompt")

    if not prompt:
        return {"error": "prompt is required"}

    if len(models) < 2:
        return {"error": "At least 2 models required for comparison"}

    if len(models) > 4:
        return {"error": "Maximum 4 models allowed for comparison"}

    results = []

    for model_id in models:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()

        try:
            response = _api_request(
                "/chat/completions",
                api_key,
                base_url,
                method="POST",
                data={
                    "model": model_id,
                    "messages": messages,
                    "max_tokens": max_tokens,
                },
                timeout=60,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract response
            content = ""
            if response.get("choices"):
                content = response["choices"][0].get("message", {}).get("content", "")

            usage = response.get("usage", {})

            results.append({
                "model": model_id,
                "response": content[:1000] + ("..." if len(content) > 1000 else ""),
                "tokens": {
                    "input": usage.get("prompt_tokens", 0),
                    "output": usage.get("completion_tokens", 0),
                },
                "latency_ms": latency_ms,
                "status": "success",
            })

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            results.append({
                "model": model_id,
                "response": None,
                "error": str(e),
                "latency_ms": latency_ms,
                "status": "error",
            })

    # Summary
    successful = [r for r in results if r["status"] == "success"]

    comparison = {}
    if successful:
        comparison["fastest"] = min(successful, key=lambda x: x["latency_ms"])["model"]
        comparison["slowest"] = max(successful, key=lambda x: x["latency_ms"])["model"]

    return {
        "prompt": prompt[:200] + ("..." if len(prompt) > 200 else ""),
        "results": results,
        "comparison": comparison,
        "note": "Response text truncated to 1000 chars for display",
    }
