# AI Agents Design

## Overview

r9s provides two ways to configure AI assistants:

- **`r9s bot`** - Simple, local configuration for personal use
- **`r9s agent`** - Full-featured, versioned agents with audit trails

## Concept Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Bot vs Agent                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   r9s bot                              r9s agent                         │
│   ────────                             ─────────                         │
│   - Simple, personal use               - Production-grade                │
│   - Single TOML file                   - Versioned configurations        │
│   - No versioning                      - Full version history            │
│   - No audit trail                     - Complete audit trail            │
│   - Quick setup                        - Governance workflows            │
│   - r9s gateway                        - Any LLM provider                │
│                                        - Tools, files, metadata          │
│                                                                          │
│   Use case:                            Use case:                         │
│   "Quick personal assistant"           "Production agents with auditing" │
│                                                                          │
│   Storage:                             Storage:                          │
│   ~/.r9s/bots/mybot.toml               ~/.r9s/agents/my-agent/           │
│                                          ├── agent.toml                  │
│                                          ├── versions/                   │
│                                          │   ├── 1.0.0.toml              │
│                                          │   └── 1.1.0.toml              │
│                                          └── audit.jsonl                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Bots (Simple)

Bots are simple TOML files for quick personal use.

### Storage

`~/.r9s/bots/{name}.toml`

```toml
description = "My personal helper"
system_prompt = '''
You are a helpful assistant.
'''
temperature = 0.7
max_tokens = 2048
```

### CLI Commands

```bash
r9s bot list                              # List all bots
r9s bot show <name>                       # Show bot details
r9s bot create <name> --system-prompt "..." # Create a bot
r9s bot delete <name>                     # Delete a bot
r9s chat --bot <name>                     # Chat with a bot
```

---

## Agents (Full-Featured)

Agents provide version control, audit trails, and multi-provider support.

### Features

- **Version Control**: Semantic versioning with immutable history
- **Audit Trail**: Every execution logged with content hash
- **Multi-Provider**: Works with Claude, GPT, Gemini, local models
- **Tools**: Function definitions for agent capabilities
- **Files**: Attach reference documents
- **Variables**: Template variables (`{{var}}`) for dynamic content

### Data Model

```
Agent
├── id: str (e.g., "agt_abc123")
├── name: str (unique identifier)
├── description: str
├── current_version: str (e.g., "1.2.0")
└── versions: [AgentVersion...]

AgentVersion (Immutable)
├── version: str (semver)
├── content_hash: sha256
├── instructions: str (system prompt)
├── model: str (e.g., "claude-sonnet-4-20250514")
├── provider: str (e.g., "anthropic", "openai")
├── tools: [ToolDefinition...]
├── files: [FileReference...]
├── variables: [str...]
├── model_params: {temperature, max_tokens, ...}
├── created_at: datetime
├── created_by: str
├── change_reason: str
├── status: "draft" | "approved" | "deprecated"
└── parent_version: str (for lineage)

AgentExecution (Audit Record)
├── execution_id: uuid
├── agent_version: str
├── content_hash: sha256 (proof of exact config)
├── request_id: str (from LLM provider)
├── model: str
├── provider: str
├── timestamp: datetime
├── input_tokens: int
├── output_tokens: int
└── session_id: str (for conversation tracking)
```

### Storage Format

**Agent Manifest** (`~/.r9s/agents/{name}/agent.toml`):

```toml
id = "agt_abc123"
name = "customer-support"
description = "Customer support assistant"
current_version = "1.2.0"
created_at = "2024-01-15T10:00:00Z"
```

**Version File** (`~/.r9s/agents/{name}/versions/1.2.0.toml`):

```toml
version = "1.2.0"
content_hash = "sha256:a1b2c3d4..."
parent_version = "1.1.0"
created_at = "2024-01-25T14:30:00Z"
created_by = "alice@example.com"
change_reason = "Added order lookup tool"
status = "approved"

model = "claude-sonnet-4-20250514"
provider = "anthropic"

[params]
temperature = 0.7
max_tokens = 4096

[instructions]
value = '''
You are a customer support agent for {{company}}.
Always be polite and professional.
'''

[variables]
company = { description = "Company name", default = "Acme Corp" }

[[tools]]
name = "lookup_order"
description = "Look up order details by order ID"
[tools.parameters]
type = "object"
properties = { order_id = { type = "string" } }
required = ["order_id"]
```

**Audit Log** (`~/.r9s/agents/{name}/audit.jsonl`):

```jsonl
{"execution_id":"exec_001","agent_version":"1.2.0","content_hash":"sha256:a1b2c3...","request_id":"msg_abc","model":"claude-sonnet-4-20250514","timestamp":"2024-01-25T10:15:32Z"}
```

### Remote Distribution (Git/HTTP)

Agent definitions can be stored in a Git repository or hosted as an archive for distribution.
The CLI can fetch bundles from a Git ref or HTTP URL and install them locally.

```
agent-bundle/
├── agent.toml
└── versions/
    ├── 1.0.0.toml
    └── 1.1.0.toml
```

Example:

```bash
r9s agent pull github:my-org/agent-definitions --path agents/support
```

The pull flow validates manifests, ensures version integrity (content hashes),
and rejects unsafe archive paths or symlinks to avoid security risks.

### CLI Commands

```bash
# Agent management
r9s agent create <name> --instructions "..." --model "claude-sonnet-4-20250514"
r9s agent list
r9s agent show <name>
r9s agent delete <name>

# Version management
r9s agent update <name> --instructions "..." --reason "Description of change"
r9s agent history <name>
r9s agent diff <name> <v1> <v2>
r9s agent rollback <name> --version <version>

# Status management
r9s agent approve <name> --version <version>
r9s agent deprecate <name> --version <version>

# Execution
r9s agent run <name> --var key=value
r9s chat --agent <name> --var key=value

# Audit
r9s agent audit <name> --last 10
r9s agent audit --request-id <id>
r9s agent export <name> --format json
r9s agent pull <ref> --path agents/support
```

### Python API

```python
from r9s import R9S

client = R9S()

# Create an agent
agent = client.agents.create(
    name="customer-support",
    instructions="You are a helpful support agent for {{company}}...",
    model="claude-sonnet-4-20250514",
    provider="anthropic",
    tools=[
        {
            "name": "lookup_order",
            "description": "Look up order by ID",
            "parameters": {"type": "object", "properties": {...}}
        }
    ],
)

# Load an existing agent
agent = client.agents.get("customer-support")
# Or specific version:
agent = client.agents.get("customer-support", version="1.2.0")

# Run the agent
response = client.agents.run(
    agent="customer-support",
    variables={"company": "Acme Corp"},
    messages=[{"role": "user", "content": "Where is my order?"}],
)

# Update agent (creates new version)
client.agents.update(
    name="customer-support",
    instructions="Updated instructions...",
    reason="Added refund policy",
)

# Query audit trail
executions = client.agents.audit.query(
    agent="customer-support",
    start_time=datetime(2024, 1, 1),
    limit=100,
)
```

### Migration from Bots

```bash
# Convert a bot to an agent
r9s agent import-bot <bot-name>

# Import all bots
r9s agent import-bots
```

---

## Provider Support

Agents work with any LLM provider:

| Provider | Models | Notes |
|----------|--------|-------|
| Anthropic | Claude 3.5, Claude 3 | Native support |
| OpenAI | GPT-4, GPT-3.5 | Native support |
| Google | Gemini Pro, Gemini Ultra | Native support |
| AWS Bedrock | Claude, Titan, etc. | Via Bedrock API |
| Local | Ollama, vLLM | Via OpenAI-compatible API |
| r9s Gateway | All above | With BYOK support |

---

## Implementation

### Core Classes

```python
# r9s/agents/models.py

@dataclass
class AgentVersion:
    version: str
    content_hash: str
    instructions: str
    model: str
    provider: str
    tools: list[dict]
    variables: list[str]
    model_params: dict
    created_at: datetime
    created_by: str
    change_reason: str
    status: str  # draft, approved, deprecated
    parent_version: Optional[str]

@dataclass
class AgentExecution:
    execution_id: str
    agent_version: str
    content_hash: str
    request_id: str
    model: str
    provider: str
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    session_id: Optional[str]
```

### Store Interface

```python
# r9s/agents/store.py

class AgentStore(Protocol):
    def get(self, name: str, version: str = "latest") -> AgentVersion: ...
    def create(self, name: str, **config) -> Agent: ...
    def update(self, name: str, **config) -> AgentVersion: ...
    def list(self) -> list[Agent]: ...
    def list_versions(self, name: str) -> list[AgentVersion]: ...

class AuditStore(Protocol):
    def record(self, execution: AgentExecution) -> None: ...
    def query(self, **filters) -> list[AgentExecution]: ...
    def export(self, format: str = "json") -> bytes: ...
```

### Local Implementation

The SDK includes a local file-based implementation:

- Agents stored in `~/.r9s/agents/`
- TOML format for human readability
- JSONL for append-only audit logs
- Git-friendly (easy to diff and commit)

---

## Implementation Specification

This section provides detailed guidance for implementing the agent system.

### File Structure

Create the following new files:

```
src/r9s/
├── agents/                      # NEW: Agent module
│   ├── __init__.py              # Export public API
│   ├── models.py                # Data classes (Agent, AgentVersion, AgentExecution)
│   ├── store.py                 # Protocol definitions
│   ├── local_store.py           # LocalAgentStore, LocalAuditStore
│   ├── versioning.py            # Semver logic, version increment
│   └── template.py              # Variable rendering ({{var}} → value)
│
├── cli_tools/
│   └── agent_cli.py             # NEW: CLI commands for agents
│
└── cli_tools/
    └── cli.py                   # MODIFY: Add agent subcommand group
```

### Existing Code to Reference

| File | Purpose | How to Use |
|------|---------|------------|
| `src/r9s/cli_tools/bots.py` | Bot storage | Pattern for TOML read/write |
| `src/r9s/cli_tools/commands.py` | Command storage | Pattern for TOML read/write |
| `src/r9s/cli_tools/cli.py` | CLI entry point | Add `agent` command group |
| `src/r9s/cli_tools/chat.py` | Chat implementation | Integration for `--agent` flag |

### Implementation Tasks

#### Phase 1: Core Data Models

1. **Create `src/r9s/agents/models.py`**
   ```python
   from dataclasses import dataclass, field
   from datetime import datetime
   from typing import Optional, Dict, List, Any
   from enum import Enum
   import hashlib
   import uuid

   class AgentStatus(str, Enum):
       DRAFT = "draft"
       APPROVED = "approved"
       DEPRECATED = "deprecated"

   @dataclass
   class Agent:
       id: str
       name: str
       description: str = ""
       current_version: str = "1.0.0"
       created_at: datetime = field(default_factory=datetime.utcnow)
       updated_at: datetime = field(default_factory=datetime.utcnow)

   @dataclass
   class AgentVersion:
       version: str
       instructions: str
       model: str
       provider: str = "r9s"
       content_hash: str = field(init=False)
       tools: List[Dict[str, Any]] = field(default_factory=list)
       files: List[Dict[str, Any]] = field(default_factory=list)
       variables: List[str] = field(default_factory=list)
       model_params: Dict[str, Any] = field(default_factory=dict)
       created_at: datetime = field(default_factory=datetime.utcnow)
       created_by: str = ""
       change_reason: str = ""
       status: AgentStatus = AgentStatus.DRAFT
       parent_version: Optional[str] = None

       def __post_init__(self):
           # Compute content hash for integrity
           content = f"{self.instructions}{self.model}{self.provider}"
           self.content_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"
           # Extract variables from instructions
           import re
           self.variables = re.findall(r'\{\{(\w+)\}\}', self.instructions)

   @dataclass
   class AgentExecution:
       agent_name: str
       agent_version: str
       content_hash: str
       execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
       request_id: str = ""
       model: str = ""
       provider: str = ""
       timestamp: datetime = field(default_factory=datetime.utcnow)
       input_tokens: int = 0
       output_tokens: int = 0
       session_id: Optional[str] = None
   ```

#### Phase 2: Local Storage

2. **Create `src/r9s/agents/local_store.py`**
   - Follow pattern from `bots.py` for TOML handling
   - Storage path: `~/.r9s/agents/{name}/`
   - Key functions:
     - `agents_root() -> Path`
     - `agent_path(name: str) -> Path`
     - `save_agent(agent: Agent) -> Path`
     - `load_agent(name: str) -> Agent`
     - `list_agents() -> List[str]`
     - `delete_agent(name: str) -> Path`
     - `save_version(name: str, version: AgentVersion) -> Path`
     - `load_version(name: str, version: str) -> AgentVersion`
     - `list_versions(name: str) -> List[str]`

3. **Create `src/r9s/agents/versioning.py`**
   - Semver parsing and incrementing
   - `parse_version(v: str) -> tuple[int, int, int]`
   - `increment_version(v: str, bump: str = "patch") -> str`
   - `compare_versions(v1: str, v2: str) -> int`

4. **Create `src/r9s/agents/template.py`**
   - Variable rendering: `{{var}}` → value
   - `render(template: str, variables: Dict[str, str]) -> str`
   - `extract_variables(template: str) -> List[str]`

#### Phase 3: CLI Commands

5. **Create `src/r9s/cli_tools/agent_cli.py`**
   - Follow pattern from `cli.py` for command structure
   - Commands to implement:
     - `agent_list()` - List all agents
     - `agent_show(name)` - Show agent details
     - `agent_create(name, instructions, model, ...)` - Create new agent
     - `agent_update(name, instructions, reason, ...)` - Create new version
     - `agent_delete(name)` - Delete agent
     - `agent_history(name)` - Show version history
     - `agent_diff(name, v1, v2)` - Diff two versions
     - `agent_rollback(name, version)` - Set current version
     - `agent_approve(name, version)` - Approve version
     - `agent_deprecate(name, version)` - Deprecate version
     - `agent_audit(name, ...)` - Query audit log
     - `agent_export(name, format)` - Export agent
     - `agent_import_bot(bot_name)` - Import from bot

6. **Modify `src/r9s/cli_tools/cli.py`**
   - Add `agent` command group
   - Register all agent subcommands

#### Phase 4: Chat Integration

7. **Modify `src/r9s/cli_tools/chat.py`**
   - Add `--agent` flag (similar to `--bot`)
   - Load agent, render variables, use as system prompt
   - Record execution to audit log

#### Phase 5: SDK API

8. **Create `src/r9s/agents/__init__.py`**
   - Export: `Agent`, `AgentVersion`, `AgentExecution`
   - Export: `LocalAgentStore`, `LocalAuditStore`
   - Export: `load_agent`, `list_agents`, `create_agent`

9. **Modify `src/r9s/__init__.py`**
   - Add `agents` property to R9S client
   - Lazy-load agents module

### Test Requirements

Create tests in `tests/`:

```
tests/
├── test_agent_models.py         # Unit tests for data classes
├── test_agent_store.py          # Unit tests for local storage
├── test_agent_versioning.py     # Unit tests for semver logic
├── test_agent_template.py       # Unit tests for variable rendering
├── test_agent_cli.py            # Integration tests for CLI
└── test_agent_integration.py    # End-to-end tests
```

Key test cases:
- Create agent, verify files created
- Update agent, verify new version created
- List agents, verify all returned
- Load specific version
- Render variables in instructions
- Audit log append and query
- Import bot as agent
- Version increment (patch, minor, major)
- Content hash consistency

### Integration Points

1. **Chat Integration**
   - In `chat.py`, when `--agent` is provided:
     ```python
     if agent_name:
         agent = load_agent(agent_name)
         version = load_version(agent_name, agent.current_version)
         system_prompt = render(version.instructions, variables)
         # After API call, record to audit log
     ```

2. **SDK Integration**
   - In `R9S` class, add:
     ```python
     @property
     def agents(self):
         from r9s.agents import AgentManager
         return AgentManager(self)
     ```

### Configuration

Environment variables:
- `R9S_AGENTS_DIR` - Override default `~/.r9s/agents/`
- `R9S_AGENT_USER` - Default user for `created_by` field

### Error Handling

Define exceptions in `src/r9s/agents/exceptions.py`:
- `AgentNotFoundError`
- `VersionNotFoundError`
- `InvalidVersionError`
- `AgentExistsError`

---

## Related Documentation

- [CLI Development Guide](cli-dev-guide.md)
- [SDK Advanced Usage](sdk-advanced.md)
