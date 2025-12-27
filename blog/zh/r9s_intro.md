# 推荐一款开源神器 r9s：让 AI 成为 Unix 管道中的标准组件

在 AI 开发工具层出不穷的今天，我们很容易迷失在各种 SDK 和 API 文档中。今天我要推荐一个开源项目 **r9s**，如果你只把它仅仅当作一个 Python client，那你可能错过了一个强大的生产力工具。

r9s 的设计哲学其实非常简单直接：**把 AI 变成 Unix 管道中即插即用的标准组件**。

而实现这一哲学的核心，就在于它对 **Bot（机器人）** 的定义。

## 1. 痛点：为什么我们厌倦了写 Prompt？

在传统的 AI CLI 工具中，我们经常需要重复编写相似的提示词。想象一下，你每天都要让 AI 帮你 code review，你可能每天都要敲一遍：

```bash
cat main.py | ai-tool --system-prompt "你是一个资深的 Python 工程师，请帮我审查这段代码，重点关注性能和安全性..."
```

这种“一次性”的调用方式不仅繁琐，而且很难保证输出质量的一致性。

## 2. 核心解法：标准化的 Bot (Standardized Bot)

r9s 认为，**Bot 应该是一个标准化的、持久化的配置单元**。

Bot 不仅仅是一个 API Endpoint，它是 **System Prompt + 模型参数 + 知识库** 的封装体。你可以把一个复杂的 Prompt Engineering 过程固化下来，变成一个可以用名字调用的 "Bot"。

### 定义一次，不仅是为了复用

你可以通过简单的命令或配置文件定义一个 Bot：

```bash
# 创建一个代码审查 Bot
r9s bot create reviewer \
    --model "claude-3-5-sonnet-20241022" \
    --system-prompt "你是一个严格的代码审查员。请以 Markdown 列表形式输出审查意见，重点关注：1. 安全漏洞 2. 异常处理 3. 变量命名规范。"
```

一旦定义完成，这个 `reviewer` 就变成了你系统里的一个“虚拟员工”。

### 管道调用的终极形态：免 Prompt

这是 r9s 最性感的地方。因为 Bot 已经包含了所有必要的上下文和指令，你在使用管道调用时，**完全不需要再写任何 Prompt**。

你的工作流将变得极其清爽：

```bash
# Code Review
cat main.py | r9s chat reviewer

# 错误日志分析（假设你定义了一个 debugger Bot）
tail -n 50 error.log | r9s chat debugger

# 文档翻译（假设你定义了一个 translator Bot）
cat README_en.md | r9s chat translator > README_zh.md
```

这时候，`r9s chat reviewer` 就像 `grep` 或 `awk` 一样，成为了一个功能单一、极其可靠的 Unix 命令。你不需要告诉它“怎么做”，只需要给它“数据”。

## 3. 原生多模态管道：文件即输入

这种管道哲学也延伸到了多模态领域。r9s 的管道原生支持二进制流，这意味着你可以直接把图片“喂”给特定的 Bot。

比如，定义一个前端验收 Bot (`ui-check`)：

```bash
# 截图并通过管道直接传送给 UI 验收 Bot
screenshot-tool --stdout | r9s chat ui-check
```

用户完全不需要关心底层的 Base64 编码、MIME type 处理，一切都在管道中自动流转。

## 4. 进阶玩法：Command 让 Bot 拥有“手脚”

除了标准化的输出，r9s 还允许通过 **Command** 给 Bot 装上“手脚”。

你可以在 Bot 的指令中嵌入 `!{...}` 语法来执行本地 Shell 命令。最经典的例子就是自动生成 Git Commit：

```bash
# 定义 commit-bot
r9s bot create commit-bot --system-prompt "请根据以下 git diff 的内容生成一个简洁的 commit message：\n\n!{git diff --cached}"

# 使用时
r9s chat commit-bot
```

当你运行这条命令时：
1. r9s 会自动在本地执行 `git diff --cached`。
2. 将执行结果填入 Prompt。
3. 发送给模型。
4. 返回生成的 Commit Message。

这使得 r9s 成为了连接 AI 模型和本地系统的强力胶水。

## 5. 全模型分发 & 一键配置

最后，作为基础设施，r9s 解决了一切“连接”问题：

-   **All-in-One Model Access**：集成了 OpenAI, Anthropic, DeepSeek, Qwen 等主流模型，一个 Key 调所有。
-   **One-click Config**：通过 `r9s set <app>`，可以一键把 `claude-code` 或其他工具的底层模型替换为 r9s 的分发通道。

## 总结

r9s 最大的贡献在于它改变了我们使用 CLI AI 的习惯：**从“编写 Prompt”转变为“调用 Bot”**。

通过将 Prompt 封装为标准化的 Bot，我们真正实现了将 AI 能力像 Unix 工具一样组合、串联，构建出高效、可复用的智能工作流。

**GitHub 地址**: [r9s-ai/r9s](https://github.com/r9s-ai/r9s)

*(安装只需一行命令：`pip install r9s` 或 `uvx r9s`)*
