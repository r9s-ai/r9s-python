# r9s: Unified AI Gateway & Developer Tools

## 🌐 **r9s Gateway** (Core Platform)

A unified AI gateway that provides **one API to rule them all**. Instead of managing multiple API keys and integrations for different AI providers, r9s gives you:

| Feature | Description |
|---------|-------------|
| **Universal API** | Single OpenAI-compatible API endpoint that routes to 40+ LLM providers (OpenAI, Anthropic, Google, Mistral, AWS Bedrock, DeepSeek, and more) |
| **API Key Management** | Create and manage API keys with fine-grained permissions and rate limits |
| **Smart Routing** | Load balancing across providers with automatic failover |
| **Usage & Billing** | Track token usage, costs, and manage billing across all providers |
| **Logs & Observability** | Full request/response logging, latency metrics, and debugging tools |
| **Multi-tenant** | Team and organization support with role-based access |

**Endpoint:** `https://api.r9s.ai/v1`

---

## 📦 **r9s SDK** (Python)

A Python SDK for seamless integration with the r9s gateway:

```python
from r9s import R9S

client = R9S(api_key="your-r9s-key")

# Chat completions
response = client.chat.create(
    model="gpt-4o",  # or claude-3, gemini-pro, etc.
    messages=[{"role": "user", "content": "Hello!"}]
)

# Image generation
images = client.images.create(
    model="gpt-image-1.5",
    prompt="A serene mountain landscape"
)
```

**Features:** Async support, streaming, all modalities (chat, images, audio, embeddings)

---

## 💻 **r9s CLI**

Command-line interface for developers:

```bash
# Chat with any model
r9s chat "Explain quantum computing"

# Generate images
r9s images generate "A futuristic city" -o city.png

# Manage local agents with custom instructions
r9s agents create my-assistant --model gpt-4o

# Run agents with skills
r9s agents run my-assistant "Help me with code review"
```

**Features:** Interactive chat, image generation/editing, agent management, skill system

---

## 🖥️ **r9s Web** (Playground)

A web-based UI for exploring r9s capabilities without writing code:

| Page | Features |
|------|----------|
| **Chat** | Conversational interface with streaming, image upload, agent selection |
| **Agents** | Create, edit, version, and manage AI agents with custom instructions |
| **Image Generation** | Generate and iteratively edit images with various models |

```bash
# Launch the web UI
r9s web
```

---

## Why r9s?

1. **One Integration** — Switch between GPT-4, Claude, Gemini without code changes
2. **Cost Control** — Track usage across all providers in one dashboard
3. **Reliability** — Automatic failover if a provider goes down
4. **Developer Experience** — SDK, CLI, and Web UI for every workflow
