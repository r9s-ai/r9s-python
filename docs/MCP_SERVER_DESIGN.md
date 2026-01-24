# r9s MCP Server Design

**Version:** 1.0.0-draft
**Status:** Proposal
**Last Updated:** 2026-01-12

---

## Overview

This document specifies the design for r9s MCP (Model Context Protocol) servers. MCP servers expose r9s Gateway capabilities to AI assistants and coding tools (Claude, Cursor, VS Code, etc.), enabling developers to manage agents, query usage, and invoke models directly from their AI-powered workflows.

---

## Strategic Value

### For Developers
- **Seamless integration**: Use r9s from within Claude/Cursor without context switching
- **Natural language operations**: "Show my token usage this month" → MCP tool call
- **AI-assisted agent management**: Let Claude help create and optimize agents

### For r9s
- **Developer adoption**: Presence in AI coding tools drives awareness
- **Stickiness**: MCP integration makes r9s part of daily workflow
- **Differentiation**: Competitors lack this integration depth

---

## MCP Server Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      MCP Client (Claude, Cursor, etc.)             │
└────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ stdio / SSE
                                    ▼
┌────────────────────────────────────────────────────────────────────┐
│                         r9s MCP Server                             │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │    Agent     │  │    Usage     │  │    Model     │            │
│  │   Manager    │  │   Tracker    │  │   Discovery  │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                 │                     │
│         └─────────────────┴─────────────────┘                     │
│                           │                                       │
│                    ┌──────┴──────┐                                │
│                    │  r9s SDK    │                                │
│                    └──────┬──────┘                                │
└───────────────────────────┼────────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                       r9s Gateway API                              │
│                    (api.r9s.ai/v1)                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## MCP Server Modules

We propose **three focused MCP servers** rather than one monolithic server:

| Server | Purpose | Risk Level |
|--------|---------|------------|
| `r9s-agents` | Agent management and invocation | Low |
| `r9s-usage` | Usage tracking and cost analytics | Low |
| `r9s-models` | Model discovery and comparison | Low |

This separation allows users to enable only what they need and simplifies security review.

---

## Module 1: r9s-agents

### Purpose
Manage and invoke r9s agents from AI assistants.

### Tools

#### `list_agents`
List available agents with optional filtering.

```typescript
{
  name: "list_agents",
  description: "List r9s agents. Returns agent names, descriptions, and current versions.",
  inputSchema: {
    type: "object",
    properties: {
      tag: {
        type: "string",
        description: "Filter by tag (e.g., 'production', 'code-review')"
      },
      status: {
        type: "string",
        enum: ["draft", "approved", "deprecated"],
        description: "Filter by status"
      },
      limit: {
        type: "number",
        default: 20,
        description: "Maximum agents to return"
      }
    }
  }
}

// Example output
{
  "agents": [
    {
      "name": "code-reviewer",
      "description": "Reviews code for security and best practices",
      "current_version": "2.1.0",
      "model": "claude-sonnet-4",
      "tags": ["code", "security"],
      "status": "approved"
    },
    ...
  ],
  "total": 12
}
```

#### `get_agent`
Get detailed agent configuration.

```typescript
{
  name: "get_agent",
  description: "Get full configuration of an agent including instructions, routing policy, and tools.",
  inputSchema: {
    type: "object",
    properties: {
      name: {
        type: "string",
        description: "Agent name"
      },
      version: {
        type: "string",
        description: "Specific version (default: current)"
      }
    },
    required: ["name"]
  }
}

// Example output
{
  "name": "code-reviewer",
  "version": "2.1.0",
  "description": "Reviews code for security and best practices",
  "instructions": "You are an expert code reviewer...",
  "model": "claude-sonnet-4",
  "routing": {
    "strategy": "failover",
    "fallback": ["gpt-4o", "gemini-1.5-pro"]
  },
  "variables": ["language", "focus_areas"],
  "tools": ["search_docs", "run_linter"]
}
```

#### `invoke_agent`
Run an agent with input. **This is the key tool** - it lets the AI assistant use r9s agents as sub-agents.

```typescript
{
  name: "invoke_agent",
  description: "Invoke an r9s agent with the given input. The agent runs through r9s Gateway with automatic routing and fallback.",
  inputSchema: {
    type: "object",
    properties: {
      name: {
        type: "string",
        description: "Agent name to invoke"
      },
      input: {
        type: "string", 
        description: "User message / prompt to send to the agent"
      },
      variables: {
        type: "object",
        description: "Variables to inject into agent template"
      },
      stream: {
        type: "boolean",
        default: false,
        description: "Stream response (if supported by MCP client)"
      }
    },
    required: ["name", "input"]
  }
}

// Example output
{
  "response": "Based on my review of the code...",
  "agent": "code-reviewer",
  "version": "2.1.0",
  "model_used": "claude-sonnet-4",
  "tokens": {
    "input": 1250,
    "output": 890
  },
  "cost_usd": 0.0067,
  "routing": {
    "strategy": "failover",
    "attempts": 1
  }
}
```

#### `create_agent`
Create a new agent.

```typescript
{
  name: "create_agent",
  description: "Create a new r9s agent with the specified configuration.",
  inputSchema: {
    type: "object",
    properties: {
      name: {
        type: "string",
        description: "Unique agent name (lowercase, hyphens allowed)"
      },
      description: {
        type: "string",
        description: "Brief description of what the agent does"
      },
      instructions: {
        type: "string",
        description: "System prompt / instructions for the agent"
      },
      model: {
        type: "string",
        description: "Primary model (e.g., 'claude-sonnet-4', 'gpt-4o')"
      },
      routing_strategy: {
        type: "string",
        enum: ["failover", "least_cost", "round_robin", "latency"],
        default: "failover"
      },
      fallback_models: {
        type: "array",
        items: { type: "string" },
        description: "Fallback models for routing"
      },
      tags: {
        type: "array",
        items: { type: "string" }
      }
    },
    required: ["name", "instructions", "model"]
  }
}
```

#### `get_agent_stats`
Get usage statistics for an agent.

```typescript
{
  name: "get_agent_stats",
  description: "Get usage statistics for an agent including invocations, tokens, costs, and routing metrics.",
  inputSchema: {
    type: "object",
    properties: {
      name: {
        type: "string",
        description: "Agent name"
      },
      period: {
        type: "string",
        enum: ["day", "week", "month"],
        default: "week"
      }
    },
    required: ["name"]
  }
}

// Example output
{
  "agent": "code-reviewer",
  "period": "week",
  "invocations": 342,
  "tokens": {
    "input": 2145000,
    "output": 567000
  },
  "cost_usd": 8.34,
  "avg_latency_ms": 2340,
  "routing": {
    "primary_success_rate": 0.94,
    "fallback_invocations": 21,
    "models_used": {
      "claude-sonnet-4": 321,
      "gpt-4o": 21
    }
  }
}
```

---

## Module 2: r9s-usage

### Purpose
Track and analyze API usage and costs.

### Tools

#### `get_usage_summary`
Get aggregated usage for the account.

```typescript
{
  name: "get_usage_summary",
  description: "Get token usage and cost summary for your r9s account.",
  inputSchema: {
    type: "object",
    properties: {
      period: {
        type: "string",
        enum: ["today", "week", "month", "all_time"],
        default: "month"
      },
      group_by: {
        type: "string",
        enum: ["model", "agent", "day", "project"],
        description: "How to group the results"
      }
    }
  }
}

// Example output (group_by: "model")
{
  "period": "month",
  "total_cost_usd": 47.82,
  "total_tokens": {
    "input": 15234000,
    "output": 4521000
  },
  "by_model": [
    {
      "model": "claude-sonnet-4",
      "tokens": { "input": 8000000, "output": 2500000 },
      "cost_usd": 31.50,
      "requests": 1250
    },
    {
      "model": "gpt-4o",
      "tokens": { "input": 5000000, "output": 1500000 },
      "cost_usd": 12.50,
      "requests": 890
    },
    ...
  ]
}
```

#### `estimate_cost`
Pre-flight cost estimation for a prompt.

```typescript
{
  name: "estimate_cost",
  description: "Estimate the cost of a prompt before running it. Useful for budget-conscious operations.",
  inputSchema: {
    type: "object",
    properties: {
      text: {
        type: "string",
        description: "The prompt text to estimate"
      },
      model: {
        type: "string",
        description: "Model to estimate for"
      },
      expected_output_tokens: {
        type: "number",
        default: 1000,
        description: "Expected output length in tokens"
      }
    },
    required: ["text", "model"]
  }
}

// Example output
{
  "model": "claude-sonnet-4",
  "input_tokens": 2500,
  "expected_output_tokens": 1000,
  "estimated_cost_usd": 0.0105,
  "cost_breakdown": {
    "input": 0.0075,
    "output": 0.0030
  }
}
```

#### `get_budget_status`
Check remaining budget/quota.

```typescript
{
  name: "get_budget_status",
  description: "Check your remaining budget and usage against limits.",
  inputSchema: {
    type: "object",
    properties: {
      project: {
        type: "string",
        description: "Specific project (optional)"
      }
    }
  }
}

// Example output
{
  "monthly_budget_usd": 100.00,
  "spent_usd": 47.82,
  "remaining_usd": 52.18,
  "percent_used": 47.8,
  "projected_monthly_usd": 68.50,
  "days_remaining": 19,
  "alerts": [
    {
      "type": "projection",
      "message": "At current rate, you'll use 68% of budget"
    }
  ]
}
```

---

## Module 3: r9s-models

### Purpose
Discover and compare available models.

### Tools

#### `list_models`
List available models with capabilities and pricing.

```typescript
{
  name: "list_models",
  description: "List available models on r9s Gateway with pricing and capabilities.",
  inputSchema: {
    type: "object",
    properties: {
      provider: {
        type: "string",
        description: "Filter by provider (anthropic, openai, google, etc.)"
      },
      capability: {
        type: "string",
        enum: ["chat", "vision", "code", "embedding", "image_gen"],
        description: "Filter by capability"
      },
      max_cost_per_1k: {
        type: "number",
        description: "Max cost per 1K tokens (filters expensive models)"
      }
    }
  }
}

// Example output
{
  "models": [
    {
      "id": "claude-sonnet-4-20250514",
      "provider": "anthropic",
      "display_name": "Claude Sonnet 4",
      "context_window": 200000,
      "capabilities": ["chat", "vision", "code"],
      "pricing": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015
      },
      "status": "available",
      "latency_p50_ms": 1200
    },
    ...
  ]
}
```

#### `compare_models`
Run the same prompt across multiple models and compare outputs.

```typescript
{
  name: "compare_models",
  description: "Run a prompt across multiple models to compare outputs, latency, and cost. Useful for model selection.",
  inputSchema: {
    type: "object",
    properties: {
      prompt: {
        type: "string",
        description: "The prompt to test"
      },
      models: {
        type: "array",
        items: { type: "string" },
        description: "Models to compare (2-4 recommended)"
      },
      max_tokens: {
        type: "number",
        default: 500,
        description: "Max tokens per response"
      }
    },
    required: ["prompt", "models"]
  }
}

// Example output
{
  "prompt": "Explain quantum entanglement in simple terms",
  "results": [
    {
      "model": "claude-sonnet-4",
      "response": "Imagine you have two coins that are magically linked...",
      "tokens": { "input": 12, "output": 245 },
      "latency_ms": 1850,
      "cost_usd": 0.0041
    },
    {
      "model": "gpt-4o",
      "response": "Quantum entanglement is like having two dice...",
      "tokens": { "input": 12, "output": 198 },
      "latency_ms": 1200,
      "cost_usd": 0.0035
    }
  ],
  "comparison": {
    "fastest": "gpt-4o",
    "cheapest": "gpt-4o",
    "most_detailed": "claude-sonnet-4"
  }
}
```

#### `get_model_status`
Check real-time status of models/providers.

```typescript
{
  name: "get_model_status",
  description: "Check real-time availability and health of models.",
  inputSchema: {
    type: "object",
    properties: {
      models: {
        type: "array",
        items: { type: "string" },
        description: "Specific models to check (default: all)"
      }
    }
  }
}

// Example output
{
  "timestamp": "2026-01-12T15:30:00Z",
  "status": [
    {
      "model": "claude-sonnet-4",
      "provider": "anthropic",
      "status": "operational",
      "latency_p50_ms": 1150,
      "error_rate_percent": 0.1
    },
    {
      "model": "gpt-4o",
      "provider": "openai",
      "status": "degraded",
      "latency_p50_ms": 3200,
      "error_rate_percent": 2.5,
      "incident": "Elevated latency in US-East region"
    }
  ]
}
```

#### `recommend_model`
Get a model recommendation based on requirements.

```typescript
{
  name: "recommend_model",
  description: "Get a model recommendation based on task type and constraints.",
  inputSchema: {
    type: "object",
    properties: {
      task: {
        type: "string",
        enum: ["code_generation", "code_review", "writing", "analysis", "chat", "translation", "summarization"],
        description: "Type of task"
      },
      priority: {
        type: "string",
        enum: ["quality", "speed", "cost"],
        default: "quality",
        description: "What to optimize for"
      },
      max_cost_per_call: {
        type: "number",
        description: "Budget constraint per call (USD)"
      },
      context_needed: {
        type: "number",
        description: "Approximate context size needed (tokens)"
      }
    },
    required: ["task"]
  }
}

// Example output
{
  "recommendation": {
    "model": "claude-sonnet-4",
    "reason": "Best code review quality, fits budget",
    "estimated_cost_per_call": 0.015
  },
  "alternatives": [
    {
      "model": "gpt-4o",
      "reason": "Faster, slightly lower quality for code",
      "estimated_cost_per_call": 0.012
    },
    {
      "model": "glm-4-9b-chat",
      "reason": "Budget option, acceptable for simple reviews",
      "estimated_cost_per_call": 0.002
    }
  ]
}
```

---

## Implementation

### CLI Command

```bash
# Start MCP server
r9s mcp serve [--module agents,usage,models] [--transport stdio|sse]

# Examples
r9s mcp serve                           # All modules, stdio
r9s mcp serve --module agents           # Only agents module
r9s mcp serve --transport sse --port 3100  # SSE transport
```

### Configuration

```toml
# ~/.r9s/config.toml

[mcp]
enabled_modules = ["agents", "usage", "models"]
default_transport = "stdio"

# Rate limiting per tool (requests per minute)
[mcp.rate_limits]
invoke_agent = 30
compare_models = 10
create_agent = 5
```

### Claude Desktop Integration

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "r9s-agents": {
      "command": "r9s",
      "args": ["mcp", "serve", "--module", "agents"]
    },
    "r9s-usage": {
      "command": "r9s",
      "args": ["mcp", "serve", "--module", "usage"]
    },
    "r9s-models": {
      "command": "r9s",
      "args": ["mcp", "serve", "--module", "models"]
    }
  }
}
```

### VS Code / Cursor Integration

```json
// settings.json
{
  "mcp.servers": {
    "r9s": {
      "command": "r9s",
      "args": ["mcp", "serve"]
    }
  }
}
```

---

## Security Considerations

### Authentication

The MCP server uses the same API key as the CLI:

```bash
# Key loaded from environment or config
export R9S_API_KEY="sk-..."

# Or from config file
# ~/.r9s/config.toml
# [auth]
# api_key = "sk-..."
```

### Scope Limitations

MCP tools are intentionally limited:

| Operation | Allowed | Reason |
|-----------|---------|--------|
| Read agents | ✅ | Low risk |
| Invoke agents | ✅ | Normal usage |
| Create agents | ✅ | Useful, audited |
| Delete agents | ❌ | Too destructive |
| Read usage | ✅ | Low risk |
| API key management | ❌ | High risk (see previous discussion) |

### Rate Limiting

All tools have per-minute rate limits to prevent abuse:

| Tool | Default Limit |
|------|---------------|
| list_agents | 60/min |
| invoke_agent | 30/min |
| create_agent | 5/min |
| compare_models | 10/min |
| get_usage_summary | 30/min |

### Audit Logging

All MCP tool calls are logged:

```jsonl
{
  "timestamp": "2026-01-12T15:30:00Z",
  "tool": "invoke_agent",
  "agent": "code-reviewer",
  "mcp_client": "claude-desktop",
  "tokens_used": 2150,
  "cost_usd": 0.0067
}
```

---

## Resources (Optional)

MCP Resources provide read-only data access. We can expose:

### `agents://`

```
agents://                     → List all agents
agents://code-reviewer        → Agent details
agents://code-reviewer/stats  → Agent statistics
```

### `usage://`

```
usage://summary         → Current month summary
usage://daily          → Daily breakdown
usage://by-model       → Usage by model
```

---

## Prompts (Optional)

Pre-built prompts for common workflows:

### `create-agent-wizard`

```typescript
{
  name: "create-agent-wizard",
  description: "Interactive wizard to help create a well-configured r9s agent",
  arguments: [
    {
      name: "purpose",
      description: "What should the agent do?",
      required: true
    }
  ]
}
```

### `optimize-agent`

```typescript
{
  name: "optimize-agent",
  description: "Analyze an agent's usage and suggest optimizations",
  arguments: [
    {
      name: "agent_name",
      description: "Agent to analyze",
      required: true
    }
  ]
}
```

---

## Rollout Plan

### Phase 1: Core (Alpha)
- `r9s-models` module (low risk, high value)
- `list_models`, `get_model_status`, `recommend_model`

### Phase 2: Agents (Beta)
- `r9s-agents` module
- `list_agents`, `get_agent`, `invoke_agent`, `get_agent_stats`
- `create_agent` (with rate limiting)

### Phase 3: Usage (GA)
- `r9s-usage` module
- `get_usage_summary`, `estimate_cost`, `get_budget_status`

### Phase 4: Advanced
- `compare_models` (expensive, rate limited)
- Resources and Prompts
- SSE transport for streaming

---

## Appendix: Full Tool Reference

| Module | Tool | Risk | Rate Limit |
|--------|------|------|------------|
| agents | list_agents | Low | 60/min |
| agents | get_agent | Low | 60/min |
| agents | invoke_agent | Low | 30/min |
| agents | create_agent | Medium | 5/min |
| agents | get_agent_stats | Low | 30/min |
| usage | get_usage_summary | Low | 30/min |
| usage | estimate_cost | Low | 60/min |
| usage | get_budget_status | Low | 30/min |
| models | list_models | Low | 60/min |
| models | get_model_status | Low | 60/min |
| models | recommend_model | Low | 30/min |
| models | compare_models | Medium | 10/min |
