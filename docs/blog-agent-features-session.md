# r9s Agent Features: A Hands-On Journey

> **Purpose**: User session design for blog post promoting r9s agent-related features.

## The Story

You're a developer who wants to:
1. Create an AI assistant for a specific task
2. Iterate on it based on feedback
3. Track changes for compliance
4. Share it with your team

This session shows how r9s agents grow with your needs: **Simple → Variables → Versioned → Production**

---

## Part 0: Configuration (1 min)

*"How do I set up my credentials?"*

Create a `.env` file in your project directory:

```bash
# .env
R9S_API_KEY=sk-your-api-key
R9S_BASE_URL=https://api.r9s.ai/v1
R9S_MODEL=gpt-5-mini
```

Or export environment variables:

```bash
export R9S_API_KEY="sk-your-api-key"
export R9S_BASE_URL="https://api.r9s.ai/v1"
export R9S_MODEL="gpt-5-mini"
```

**Takeaway**: r9s automatically loads `.env` from your current directory. No extra setup needed.

---

## Part 1: Quick Start with Agents (2 min)

*"I want a vocabulary learning assistant"*

First, create a prompt file:

```bash
cat > vocab-tutor.md << 'EOF'
You are an English vocabulary tutor. When given a word:

1. **Definition**: Clear, simple explanation
2. **Pronunciation**: IPA notation
3. **Example sentences**: 2-3 natural examples
4. **Synonyms**: 3-5 related words with nuance differences
5. **Common collocations**: Frequently paired words
6. **Etymology**: Brief origin (if interesting)

Keep explanations concise. Use 中文 translations when helpful for Chinese learners.
EOF
```

Then create the agent:

```bash
# Create agent from file (using @filename convention)
r9s agent create vocab-tutor \
  --instructions @vocab-tutor.md \
  --model gpt-5-mini

# Use it immediately
r9s chat --agent vocab-tutor
You> ephemeral
Agent> **ephemeral** /ɪˈfem.ər.əl/

**Definition**: Lasting for a very short time; transitory.
(中文: 短暂的，转瞬即逝的)

**Example sentences**:
- The ephemeral beauty of cherry blossoms draws millions of visitors each spring.
- Social media fame is often ephemeral—here today, gone tomorrow.

**Synonyms**:
- transient (more formal)
- fleeting (emphasizes speed)
- momentary (very brief)
- short-lived (casual)

**Collocations**: ephemeral nature, ephemeral beauty, ephemeral moment

**Etymology**: From Greek *ephēmeros* "lasting only a day" (epi- "on" + hēmera "day")

tokens: 45 in / 186 out
```

**Takeaway**: Use `--instructions @filename` to load prompts from files (like `curl`). Easier to edit and version control.

---

## Part 2: Power Up with Commands (3 min)

*"I want to review my staged git changes automatically"*

```bash
# Create a command with shell injection
r9s command create review-diff --prompt 'Review this code diff for issues:

```diff
!{git diff --staged}
```

Focus on: bugs, security, performance, readability.'

# See what it renders (debug mode)
r9s command render review-diff
# Shows the actual diff injected into the prompt

# Run it before every commit
r9s command run review-diff
```

Sometimes the model needs more context than just the diff. You can include the full file content:

```bash
# Enhanced version with file context
r9s command create review-diff --prompt 'Review this code:

!{echo "=== DIFF ===" && git diff --staged && echo "" && echo "=== FILE CONTEXT ===" && git diff --staged --name-only | while read f; do echo "--- $f ---"; head -100 "$f"; done}

Focus on: bugs, security, performance, readability.'
```

**Takeaway**: Commands inject live data (`!{shell}`, `@{file}`) into prompts. Add context as needed for better reviews.

---

## Part 3: Variables and Customization (3 min)

*"I want to customize the tutor for different learners"*

```bash
# Upgrade vocab-tutor with template variables
r9s agent update vocab-tutor \
  --instructions 'You are a {{target_language}} vocabulary tutor for {{native_language}} speakers at {{level}} level.

IMPORTANT: All explanations must be in {{native_language}}. Only use {{target_language}} for the vocabulary words, examples, and translations.

When given a word:
1. **Definition**: Explain in {{native_language}}, show the {{target_language}} word
2. **Pronunciation**: IPA notation + phonetic hints familiar to {{native_language}} speakers
3. **Example sentences**: {{example_count}} sentences in {{target_language}} with {{native_language}} translations
4. **Related words**: Synonyms and antonyms explained in {{native_language}}
5. **Common collocations**: Show {{target_language}} phrases with {{native_language}} meanings
6. **Memory tip**: Mnemonic connecting to {{native_language}} words or sounds' \
  --model gpt-5-mini

# See auto-extracted variables
r9s agent show vocab-tutor
# Variables: target_language, native_language, level, example_count, formality

# Use it for a beginner German learner
r9s chat --agent vocab-tutor \
  --var target_language=German \
  --var native_language=English \
  --var level=beginner \
  --var example_count=2 \
  --var formality=casual

You> Schmetterling
Agent> **Schmetterling** /ˈʃmɛtɐlɪŋ/
(English: butterfly)

**Pronunciation tip**: "shmet-ter-ling" - stress on first syllable

**Example sentences**:
- Der Schmetterling fliegt im Garten. (The butterfly flies in the garden.)
- Ich sehe einen bunten Schmetterling. (I see a colorful butterfly.)

**Related words**:
- die Raupe (caterpillar) - what it starts as
- die Motte (moth) - nocturnal cousin

**Collocations**: bunter Schmetterling, Schmetterling fangen

**Memory tip**: Think "smash + butter + fling" - imagine a butterfly flinging butter!

tokens: 67 in / 189 out
```

**Takeaway**: Variables make agents reusable. Same agent, different learners.

---

## Part 4: Versioning and Iteration (4 min)

*"This is working great for beginners. Now I want to level up for advanced learners."*

Your vocab-tutor works well for language learners. But what about native speakers aiming for precise, sophisticated expression—the kind you'd find in *The Economist* or academic writing?

### 4.1 Update with Version Control

```bash
# Upgrade vocab-tutor for advanced users
r9s agent update vocab-tutor \
  --instructions 'You are a vocabulary consultant for advanced English users seeking precision and sophistication.

When given a word:

1. **Core meaning**: Precise definition with connotation (positive/negative/neutral)
2. **Register**: Where this word belongs (academic, journalistic, literary, conversational)
3. **Precision vs alternatives**: How it differs from near-synonyms—what nuance does THIS word convey that others don't?
4. **Sophisticated usage**: 2 examples from quality writing (NYT, academic papers, literature)
5. **Pitfalls**: Common misuses, even among educated speakers
6. **Power move**: One sentence showing the word used to convey subtle meaning effectively

Target audience: Native speakers, graduate students, professionals who want to write and speak with precision.' \
  --bump major \
  --reason "Redesigned for advanced users: added register, precision analysis, and sophisticated usage examples"

# View version history
r9s agent history vocab-tutor
# v1.0.0 (2025-01-05) - Initial beginner version
# v2.0.0 (2025-01-06) - Redesigned for advanced users [CURRENT]
```

### 4.2 See the Difference

```bash
# Compare what changed
r9s agent diff vocab-tutor 1.0.0 2.0.0
```

### 4.3 Try the Advanced Version

```bash
r9s chat --agent vocab-tutor

You> nuance
Agent> **nuance** /ˈnjuː.ɑːns/

**Core meaning**: A subtle distinction or variation in meaning, expression, or response. *Connotation*: Positive—suggests sophistication and careful thought.

**Register**: Academic, journalistic, literary. Signals educated discourse. Avoid overuse in casual speech (can sound pretentious).

**Precision vs alternatives**:
- *subtlety*: Broader; nuance specifically implies fine gradations
- *distinction*: More binary; nuance suggests a spectrum
- *shade*: Informal equivalent ("shades of meaning")

**Sophisticated usage**:
- "The diplomat's response was full of nuance, acknowledging grievances without assigning blame."
- "Her analysis captured nuances that the quantitative study missed entirely."

**Pitfalls**:
- Don't use as a verb ("to nuance an argument")—controversial and often criticized
- Avoid "very nuanced" (redundant; nuance already implies degree)

**Power move**: "His objection wasn't opposition—it was nuance, a refinement that strengthened the proposal."

tokens: 72 in / 234 out
```

### 4.4 Governance for Production

```bash
# Mark as production-ready
r9s agent approve vocab-tutor --version 2.0.0

# Check usage for the month
r9s agent audit vocab-tutor --last 50
# Shows: execution_id, timestamp, model, tokens_in, tokens_out

# If v2 is too verbose, rollback
r9s agent rollback vocab-tutor --version 1.0.0
```

**Takeaway**: Version control for prompts—iterate boldly, rollback safely, audit everything.

---

## Key Agent Features

| Feature | Description |
|---------|-------------|
| Instructions | System prompt defining agent behavior |
| Variables | `{{custom}}` placeholders for runtime customization |
| File injection | `@{path}` to include file contents |
| Versioning | Semantic versioning (major.minor.patch) |
| Audit trail | Full execution history with token counts |
| Status workflow | DRAFT → APPROVED → DEPRECATED |
| Team sharing | Export/Import as JSON |

---

## Blog Post Structure Suggestion

1. **Hook**: "Your prompts deserve version control too"
2. **Problem**: Prompt drift, no audit trail, manual iteration
3. **Solution Journey**: Simple Agent → Variables → Versioned → Production
4. **Key Moments**:
   - First agent creation
   - First variable substitution
   - First version bump
   - First audit query
   - First rollback
5. **CTA**: `pip install r9s` + link to docs

---

## Target Audience

- Developers using LLMs in their workflow
- Teams needing prompt governance
- DevOps/Platform engineers building AI tooling

## Estimated Read Time

- Session walkthrough: 13 minutes
- Blog post: 8-10 minute read
