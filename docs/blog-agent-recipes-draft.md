# r9s Agent Recipes: Developer Workflow Helpers

> **Purpose**: Draft content for a future blog post showcasing practical agent examples for developers.

---

## Real-World Workflow

*"Show me the daily workflow"*

```bash
# Morning: Check what changed
r9s agent history code-reviewer

# Before commit: Quick review
git add -p
r9s command run review-diff

# In PR discussion: Deep review with context
r9s chat --agent code-reviewer \
  --var role=security \
  --var language=Python \
  --var focus_areas="OWASP top 10"

You> Review the auth module changes in PR #42
# Paste the code...

# End of sprint: Audit report
r9s agent audit code-reviewer --last 50 > sprint-audit.json
```

---

## Agent Gallery - Quick Helpers

*"What else can I use this for?"*

```bash
# Git commit message writer
r9s agent create commit-msg \
  --instructions "Write a conventional commit message for this diff.
Format: type(scope): description
Types: feat, fix, docs, refactor, test, chore
Be concise. Focus on the 'why', not the 'what'." \
  --model gpt-5-mini

# Error explainer
r9s agent create explain-error \
  --instructions "Explain this error in plain English.
1. What happened (root cause)
2. Why it happened
3. How to fix it
Include relevant documentation links if applicable." \
  --model gpt-5-mini

# Documentation writer
r9s agent create doc-writer \
  --instructions "Write docstrings for the given code.
Style: Google/NumPy format
Include: description, args, returns, raises, example usage
Match the existing codebase style if context is provided." \
  --model gpt-5-mini

# SQL query optimizer
r9s agent create sql-reviewer \
  --instructions "Analyze SQL queries for:
- N+1 query patterns
- Missing indexes
- Inefficient joins
- Security issues (injection risks)
Suggest optimizations with EXPLAIN plan hints." \
  --model gpt-5-mini

# Test case generator
r9s agent create test-ideas \
  --instructions "Generate test cases for the given function.
Include: happy path, edge cases, error cases, boundary values.
Format as bullet points, not code. Focus on what to test, not how." \
  --model gpt-5-mini

# API design reviewer
r9s agent create api-reviewer \
  --instructions "Review REST/GraphQL API designs for:
- Naming consistency (plural nouns, kebab-case)
- HTTP method correctness
- Status code appropriateness
- Versioning strategy
- Breaking change risks" \
  --model gpt-5-mini
```

**Usage examples:**

```bash
# Commit message from staged changes
git diff --staged | r9s chat --agent commit-msg

# Explain a Python traceback
r9s chat --agent explain-error
You> Paste: TypeError: 'NoneType' object is not subscriptable...

# Generate docs for a function
r9s chat --agent doc-writer
You> def calculate_discount(price, percentage, max_discount=None): ...
```

**Takeaway**: Build a personal toolkit of specialized agents - each one a focused expert.

---

## Blog Post Ideas

This content could become:
1. **"r9s Agent Recipes: A Developer's CLI Toolkit"** - Focus on practical daily workflow
2. **"10 Agents Every Developer Should Create"** - Listicle format
3. **"From Code Review to Commit: Automating Your Git Workflow with r9s"** - Git-focused deep dive
