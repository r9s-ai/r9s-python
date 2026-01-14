# Skill Script Execution Spec

## Overview

Enable r9s agents to execute scripts from skills during response generation, compliant with the [agentskills.io](https://agentskills.io) specification.

## Current State

- `!{cmd}` syntax works in **prompts** (template expansion before LLM)
- LLM **output** cannot execute commands without external extensions
- Skills can define `scripts/` directory but scripts are not executable

## Goal

Allow LLMs to invoke skill scripts in their responses, with the output either:
1. **Executed for side-effects** (e.g., TTS, notifications)
2. **Captured and injected** back into context (e.g., data lookup)

## Proposed Syntax

Use existing `!{...}` syntax in LLM output:

```
!{say "hello world"}           # Side-effect only (TTS)
!{scripts/lookup.py "term"}    # Capture output
```

New modifier for side-effect-only execution:

```
!{! say "hello"}               # Execute, no output capture (side-effect)
!{scripts/say.sh "hello"}      # Execute, capture output
```

Or use a different delimiter for side-effects:

```
%{say "hello"}                 # Side-effect (current extension approach)
!{scripts/lookup.py "term"}    # Capture output
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      chat_cli.py                             │
├─────────────────────────────────────────────────────────────┤
│  1. LLM streams response                                     │
│  2. Post-processor detects !{...} or %{...} patterns        │
│  3. Resolves script path (skill scripts/ or system command) │
│  4. Checks ScriptPolicy for permission                       │
│  5. Executes via subprocess                                  │
│  6. For side-effects: strips pattern from output             │
│  7. For capture: injects result (future: agentic loop)       │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Tasks

### Phase 1: Side-Effect Execution (TTS use case)

1. **Add post-response processor in `chat_cli.py`**
   - After `run_after_response_extensions()`, process `%{...}` patterns
   - Execute commands, strip from displayed/stored output
   - No extension needed - built into chat

2. **Respect ScriptPolicy**
   - Check `allow_scripts` flag from skill
   - Whitelist allowed commands (e.g., `say`, `open`, skill scripts)
   - Sandbox options (timeout, no network, etc.)

3. **Resolve skill scripts**
   - `%{scripts/say.sh "word"}` → `~/.r9s/skills/<skill>/scripts/say.sh`
   - Validate script exists and is executable

### Phase 2: Output Capture (Data lookup use case)

1. **Agentic loop support**
   - LLM outputs `!{scripts/lookup.py "term"}`
   - r9s executes, captures output
   - Injects result back as context
   - LLM continues with new information

2. **Streaming considerations**
   - Buffer output until pattern complete
   - Execute mid-stream or wait for full response?

### Phase 3: Security Hardening

1. **ScriptPolicy enforcement**
   ```python
   @dataclass
   class ScriptPolicy:
       allow_scripts: bool = False
       allow_network: bool = False
       allow_filesystem: bool = False
       timeout_seconds: int = 30
       allowed_commands: List[str] = field(default_factory=list)
   ```

2. **Confirmation prompts**
   - Interactive: prompt user before execution
   - Non-interactive: require `-y` flag or policy

3. **Sandboxing**
   - Run in restricted subprocess
   - Limit environment variables
   - Chroot or container isolation (future)

## File Changes

### `src/r9s/cli_tools/chat_cli.py`

```python
def _process_script_commands(text: str, skills: List[Skill], policy: ScriptPolicy) -> str:
    """Execute %{...} commands in LLM output and strip from text."""
    pattern = re.compile(r'%\{(.+?)\}', re.DOTALL)

    def execute_and_strip(match):
        cmd = match.group(1).strip()
        if not policy.allow_scripts:
            return ""  # Strip but don't execute

        # Resolve skill scripts
        resolved_cmd = _resolve_skill_script(cmd, skills)

        # Check allowed commands
        if not _is_allowed(resolved_cmd, policy):
            return ""

        # Execute for side-effect
        try:
            subprocess.run(resolved_cmd, shell=True, timeout=policy.timeout_seconds)
        except Exception:
            pass

        return ""  # Strip from output

    return pattern.sub(execute_and_strip, text)
```

### `src/r9s/skills/models.py`

Already has `ScriptPolicy` - extend with more controls.

### `src/r9s/skills/loader.py`

Add function to resolve script paths:

```python
def resolve_skill_script(cmd: str, skills: List[Skill]) -> Optional[str]:
    """Resolve 'scripts/foo.sh' to full path if in loaded skills."""
    if not cmd.startswith("scripts/"):
        return None

    script_name = cmd.split()[0]  # e.g., "scripts/say.sh"

    for skill in skills:
        for script in skill.scripts:
            if script == script_name or script.endswith("/" + script_name):
                return str(skill_path(skill.name) / script_name)

    return None
```

## Skill Example

```
say/
├── SKILL.md
└── scripts/
    └── speak.sh
```

**SKILL.md:**
```yaml
---
name: say
description: Text-to-speech for vocabulary learning and pronunciation
compatibility: macOS (requires 'say' command)
---

# Text-to-Speech Skill

To speak text aloud, use:

%{scripts/speak.sh "text to speak"}

Or for system say command:

%{say "text to speak"}
```

**scripts/speak.sh:**
```bash
#!/bin/bash
say -v "${R9S_TTS_VOICE:-Alex}" "$1"
```

## Usage

```bash
# Skills with scripts enabled
r9s chat --agent vocab-tutor --allow-scripts

# Or via agent config
skills = ["say"]
script_policy = { allow_scripts = true, allowed_commands = ["say", "scripts/*"] }
```

## Migration

1. Existing `say_ext.py` extension → deprecated
2. Built-in `%{...}` processing in chat_cli
3. Extension mechanism remains for advanced use cases

## Open Questions

1. **Syntax choice**: `%{...}` vs `!{! ...}` vs `@{...}` for side-effects?
2. **Streaming**: Process during stream or after complete response?
3. **Confirmation**: Always prompt, never prompt, or configurable?
4. **Skill script discovery**: Explicit allow-list or auto-discover from loaded skills?

## References

- [agentskills.io specification](https://agentskills.io/specification)
- [r9s template_renderer.py](../src/r9s/cli_tools/template_renderer.py) - existing `!{...}` handling
- [r9s skills models.py](../src/r9s/skills/models.py) - ScriptPolicy
