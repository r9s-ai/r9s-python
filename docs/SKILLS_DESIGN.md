# Agent Skills Design

## Overview

r9s supports the [Agent Skills open standard](https://agentskills.io/specification) to provide reusable, shareable capabilities for agents. Skills package procedural knowledge into modules that agents can discover and apply.

This document focuses on the initial CLI-driven experience and the data model required to load skills locally, with a path toward remote installation and agent integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Skill Sources                             │
├───────────────┬─────────────────┬───────────────────────────┤
│ Local         │ r9s Registry    │ Remote URLs               │
│ ~/.r9s/skills │ registry.r9s.ai │ github:, https://         │
├───────────────┼─────────────────┼───────────────────────────┤
│ No auth       │ Public, no auth │ Optional auth header      │
└───────────────┴─────────────────┴───────────────────────────┘
                           │
                           ▼
                 ┌─────────────────┐
                 │  r9s skill CLI  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   r9s agent     │
                 │  skills = [...] │
                 └─────────────────┘
```

## Skill Reference Formats

| Format | Example | Description |
|--------|---------|-------------|
| Local name | `code-review` | From `~/.r9s/skills/code-review/` |
| r9s registry | `r9s:code-review` | From `registry.r9s.ai/skills/code-review` |
| GitHub | `github:owner/repo` | From GitHub repository |
| GitHub with path | `github:owner/repo/path/to/skill` | Specific path in repo |
| HTTPS URL | `https://example.com/skill.zip` | Direct download |

### Reference Resolution

1. **Local name**: resolve to `~/.r9s/skills/<name>`.
2. **r9s registry**: map `r9s:<name>` → `https://registry.r9s.ai/skills/<name>`.
3. **GitHub**: map `github:owner/repo[/path]` → `https://github.com/<owner>/<repo>/archive/refs/heads/main.zip` and then extract `path` if provided.
4. **HTTPS**: download zip directly; validate top-level directory has `SKILL.md`.

If a ref cannot be resolved, return a `SkillNotFoundError` with a hint for valid formats.

## Skill Directory Structure

Following the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
├── SKILL.md              # Required: metadata + instructions
├── scripts/              # Optional: helper scripts
├── references/           # Optional: documentation
└── assets/               # Optional: resources
```

### SKILL.md Format

```markdown
---
name: code-review
description: Comprehensive code review workflow with security and performance checks
license: MIT
compatibility: requires git
metadata:
  author: r9s-ai
  version: 1.0.0
  tags: [code, review, security]
allowed-tools: bash rg
---

# Code Review Skill

## Overview

Brief description loaded at startup (~100 tokens).

## Instructions

Detailed implementation guidance loaded when skill is activated (<5000 tokens recommended).

## Resources

- `scripts/lint.sh` - Run linting checks
- `references/checklist.md` - Review checklist
```

### Required Fields

- **name**: 1-64 chars, lowercase alphanumeric + hyphens, matches directory name
- **description**: 1-1024 chars, keywords for agent discovery

### Optional Fields

- **license**: Skill license terms
- **compatibility**: Environment requirements (up to 500 chars)
- **metadata**: Key-value pairs (author, version, tags, etc.)
- **allowed-tools**: Space-delimited pre-approved tools

### Validation Rules

- `name` must match `^[a-z0-9-]{1,64}$` and directory name.
- `description` length: 1–1024.
- YAML frontmatter must parse and be a mapping.
- `allowed-tools` is a list of tool identifiers separated by spaces in YAML or list form.
- Any additional keys in frontmatter are stored under `metadata` but must be JSON-serializable.

---

## Local Storage

```
~/.r9s/
├── skills/
│   ├── code-review/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── lint.sh
│   └── api-design/
│       ├── SKILL.md
│       └── references/
│           └── openapi-template.yaml
└── agents/
    └── reviewer/
        ├── agent.toml          # skills = ["code-review", "r9s:security-audit"]
        └── versions/
```

---

## CLI Commands

### Skill Management

```bash
# Create local skill
r9s skill create <name>                    # Interactive
r9s skill create <name> --edit             # Open $EDITOR
r9s skill create <name> -f ./SKILL.md      # From file

# List and inspect
r9s skill list                             # List local skills
r9s skill show <name>                      # Show skill details
r9s skill validate <name>                  # Validate against spec

# Install from sources
r9s skill install <ref>                    # Install skill
r9s skill install r9s:code-review          # From r9s registry
r9s skill install github:anthropics/skills/code-review
r9s skill install https://example.com/skill.zip
r9s skill install https://internal.co/skill --header "Authorization: Bearer $TOKEN"

# Remove
r9s skill delete <name>                    # Delete local skill
```

### Agent-Skill Integration

```bash
# Create agent with skills
r9s agent create reviewer --skills code-review,r9s:security-audit --model gpt-4

# Manage agent skills
r9s agent skill add <agent> <skill-ref>    # Add skill to agent
r9s agent skill remove <agent> <skill>     # Remove skill from agent
r9s agent skill list <agent>               # List agent's skills
```

---

## Data Models

### Skill Metadata

```python
@dataclass
class SkillMetadata:
    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_tools: List[str] = field(default_factory=list)
```

### Skill

```python
@dataclass
class Skill:
    name: str
    description: str
    instructions: str                      # Full SKILL.md body
    source: str                            # "local", "r9s", "github", "https"
    source_ref: Optional[str] = None       # Original reference
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    scripts: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
```

### Agent Update

```python
@dataclass
class AgentVersion:
    # ... existing fields ...
    skills: List[str] = field(default_factory=list)  # Skill references
```

---

## Implementation Phases

### Phase 1: Local Skills (MVP)

1. Create `src/r9s/skills/` module
   - `models.py` - SkillMetadata, Skill dataclasses
   - `parser.py` - Parse SKILL.md (YAML frontmatter + Markdown)
   - `local_store.py` - CRUD for `~/.r9s/skills/`
   - `validator.py` - Validate against Agent Skills spec
   - `exceptions.py` - SkillNotFoundError, InvalidSkillError

2. Create `src/r9s/cli_tools/skill_cli.py`
   - `skill create`, `skill list`, `skill show`, `skill delete`, `skill validate`

3. Update `src/r9s/cli_tools/cli.py`
   - Add `skill` command group

### Phase 2: Remote Skills

4. Create `src/r9s/skills/registry.py`
   - Fetch from r9s registry (`registry.r9s.ai/skills/`)
   - Parse skill references (r9s:, github:, https:)

5. Create `src/r9s/skills/installer.py`
   - `skill install` implementation
   - Download, extract, validate, save to local

6. Add auth support
   - `--header` flag for custom auth
   - Config file support for persistent auth

### Phase 3: Agent Integration

7. Update `src/r9s/agents/models.py`
   - Add `skills: List[str]` to AgentVersion

8. Update `src/r9s/cli_tools/agent_cli.py`
   - `agent create --skills`
   - `agent skill add/remove/list`

9. Update `src/r9s/cli_tools/chat_cli.py`
   - Load agent skills into context
   - Progressive disclosure (metadata first, full on activation)

### Phase 4: Registry Publishing (Future)

10. `r9s skill publish <name>` - Publish to r9s registry
11. Skill search and discovery
12. Versioned skills

---

## Progressive Disclosure

Following the Agent Skills spec:

1. **Startup**: Load skill metadata only (~100 tokens per skill)
2. **Activation**: Load full SKILL.md body when relevant (<5000 tokens)
3. **On-demand**: Load scripts/references/assets when needed

```python
class SkillLoader:
    def load_metadata(self, name: str) -> SkillMetadata:
        """Load only frontmatter for context efficiency."""

    def load_full(self, name: str) -> Skill:
        """Load complete skill with instructions."""

    def load_resource(self, name: str, path: str) -> bytes:
        """Load specific resource on demand."""
```

---

## Error Handling

- **Invalid skill**: raise `InvalidSkillError` with a validation report.
- **Missing skill**: raise `SkillNotFoundError` for local or remote refs.
- **I/O errors**: surface `OSError` with user-facing guidance in the CLI.
- **Remote download**: include HTTP status and retryable hint when applicable.

CLI should convert errors into human-readable messages and non-zero exit codes.

---

## Configuration

### ~/.r9s/config.toml

```toml
[skills]
# Default registry
registry = "https://registry.r9s.ai/skills"

# Custom sources with auth
[skills.sources.internal]
url = "https://internal.company.com/skills"
auth = "bearer:${INTERNAL_TOKEN}"

[skills.sources.github-private]
url = "https://raw.githubusercontent.com/myorg/private-skills"
auth = "token:${GITHUB_TOKEN}"
```

---

## API Design (Future SaaS)

### Registry API

```
GET  /skills                    # List all public skills
GET  /skills/{name}             # Get skill metadata
GET  /skills/{name}/download    # Download skill archive
POST /skills                    # Publish new skill (authenticated)
```

### Response Format

```json
{
  "name": "code-review",
  "description": "Comprehensive code review workflow",
  "version": "1.0.0",
  "author": "r9s-ai",
  "downloads": 1234,
  "download_url": "https://registry.r9s.ai/skills/code-review/1.0.0.zip"
}
```

---

## File Structure

```
src/r9s/
├── skills/
│   ├── __init__.py
│   ├── models.py           # Skill, SkillMetadata
│   ├── parser.py           # SKILL.md parser
│   ├── local_store.py      # Local skill storage
│   ├── registry.py         # Remote registry client
│   ├── installer.py        # Skill installer
│   ├── validator.py        # Spec validation
│   └── exceptions.py       # Skill exceptions
└── cli_tools/
    └── skill_cli.py        # CLI handlers
```

---

## Test Requirements

```
tests/
├── test_skill_models.py        # Unit tests for dataclasses
├── test_skill_parser.py        # SKILL.md parsing tests
├── test_skill_store.py         # Local storage tests
├── test_skill_validator.py     # Validation tests
├── test_skill_installer.py     # Install flow tests
└── test_skill_cli.py           # CLI integration tests
```

---

## Open Questions

- Should `allowed-tools` be enforced in CLI, or only passed to the agent runtime?
- How should git-based sources resolve default branches (main vs master)?
- Should `skill install` support signed archives for integrity verification?

---

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Anthropic: Equipping agents with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Simon Willison: Agent Skills](https://simonwillison.net/2025/Dec/19/agent-skills/)
