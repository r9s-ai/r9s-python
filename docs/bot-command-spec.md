# Bot / Command 规范

本文定义 r9s chat 的“预设配置”拆分方案：

- **Bot**：只负责 `system_prompt`（人格/规则）。
- **Command**：只负责 `prompt` 模板；注册后成为 `r9s chat` 内的 **slash command**（`/xxx`），也支持在命令行非交互执行。

> 说明：项目尚未发布，本方案不考虑兼容早期草案。

---

## 1) 存储位置

### 1.1 Bots

- 目录：`~/.r9s/bots/`
- 文件名：`<name>.toml`

### 1.2 Commands

- 目录：`~/.r9s/commands/`
- 文件名：`<name>.toml`

### 1.3 name 约束

建议：`[a-zA-Z0-9][a-zA-Z0-9._-]*`

---

## 2) Bot TOML（仅 system_prompt）

Bot 只支持配置 **system prompt 文本**。

示例：`~/.r9s/bots/reviewer.toml`

```toml
description = "Code review assistant"
system_prompt = """
You are a strict code reviewer.
Focus on correctness, security, and readability.
"""
```

字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `description` | string | 否 | 简短说明 |
| `system_prompt` | string（多行） | 否 | system prompt |
| `temperature` | float | 否 | 采样温度（影响发散/稳定） |
| `top_p` | float | 否 | nucleus sampling |
| `max_tokens` | int | 否 | 最大输出 token 数 |
| `presence_penalty` | float | 否 | 存在惩罚 |
| `frequency_penalty` | float | 否 | 频率惩罚 |

约束：

- 不支持 `system_prompt_file`。
- 不支持 `model` / `base_url`（这些属于环境/连接配置，仍通过 `--model`/`R9S_MODEL`、`--base-url`/`R9S_BASE_URL`、`r9s set` 管理）。
- 以上生成参数会在 `r9s chat <bot>` 以及 `r9s command run --bot <bot>` 调用模型时自动带上，用于赋予该 bot 稳定的“输出风格/个性”。

用法：

- 交互：`r9s chat reviewer`
- 非交互需要 stdin 作为用户消息：`echo "hello" | r9s chat reviewer`

---

## 3) Command TOML（仅 prompt 模板）

Command 只支持配置 **prompt 模板**。

示例：`~/.r9s/commands/commit-msg.toml`

```toml
description = "Generate a commit message from staged diff"
prompt = """
Please generate a commit message from this diff:

!{git diff --staged}
"""
```

字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `description` | string | 否 | 简短说明 |
| `prompt` | string（多行） | 是 | prompt 模板 |

模板语法：

- `{{args}}`：替换为 slash command 的参数字符串
  - 例：输入 `/summarize focus on risks`，则 `{{args}} == "focus on risks"`
- `!{ ... }`：执行本地 shell 命令（默认 `bash -lc ...`），用 stdout 替换

---

## 4) Shell 执行策略（默认安全）

当模板渲染包含 `!{...}` 时：

- 每条命令执行前都需要 **用户确认**。
- CLI 参数 `-y` 可跳过确认（等价于“我信任本地模板命令执行”）。
- 每次执行都需要向 stderr 输出提示（包含命令文本）。

---

## 5) `r9s chat` 中的 slash command 注册

当 `r9s chat` 启动（交互模式）时：

1) 扫描并加载所有 `~/.r9s/commands/*.toml`
2) 将每个 command 注册为 `/name`

在 chat 中调用：

- 输入：`/name ...args...`
- 行为：加载对应 command 的 `prompt`，替换 `{{args}}`，按策略执行 `!{...}`，将渲染后的文本作为 **单条 user message** 发给模型。

内置命令仍保留：

- `/exit`、`/clear`、`/help`

未知 `/xxx`：

- 若匹配已注册 command，则执行；
- 否则提示 unknown command。

---

## 6) 命令行非交互执行 command

建议新增：

- `r9s command run <name> [args...]`
  - `args...` 拼接为 `{{args}}`
  - stdin 可选（shell 命令也可以读取 stdin，自行决定是否使用）

可选调试命令：

- `r9s command render <name> [args...]`（仅渲染并输出最终 prompt，不请求 API）

Shell 确认：

- `run/render` 都支持 `-y` 跳过 `!{...}` 的确认。

---

## 7) 明确不做的事情

- 不提供与旧“bot 同时支持 prompt”方案的兼容/迁移。
- 不支持 `system_prompt_file`。
- 不引入额外模板变量（仅 `{{args}}` 与 `!{...}`）。
- 不持久化 command 的参数历史。
