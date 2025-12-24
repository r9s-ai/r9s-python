## 基础功能
提供r9s的sdk，方便用户在python中接入r9s
## 扩展功能
### 对话
```
r9s chat --model "" --system-prompt "xxx" 
```
model: 可通过环境变量设置，如：export R9S_MODEL=xxx

支持从标准输入获取内容发给大模型，并流式的输出结果；也支持交互式多轮对话与会话历史持久化。

#### 关键能力
- **stdin 模式**：`echo "你好" | r9s chat --model xxx`（适合脚本/管道）
- **交互模式**：直接运行 `r9s chat --model xxx`，逐行输入，多轮对话自动携带上下文
- **system prompt**：`--system-prompt` / `--system-prompt-file` / `R9S_SYSTEM_PROMPT`
- **会话历史**：默认写入 `~/.r9s/chat/`；`--no-history` 可关闭；`--history-file` 可指定路径
- **恢复对话**：`r9s chat resume` 进入交互式选择，从 `~/.r9s/chat/` 选择并恢复继续对话
- **对话扩展（extensions）**：通过 `--ext` 或 `R9S_CHAT_EXTENSIONS` 加载扩展模块/脚本，实现输入/输出/请求前后处理

#### 扩展点约定（最小接口）
扩展模块需提供 `register(registry)` / `get_extension()` / `EXTENSION` / `extension` 之一，并可选实现：
- `on_user_input(text, ctx) -> str`
- `before_request(messages, ctx) -> list[dict]`
- `on_stream_delta(delta, ctx) -> str`
- `after_response(text, ctx) -> str`
### 一键设置应用接入r9s
```
r9s set/reset [app]
```
app: 如codex / cc / qwen
