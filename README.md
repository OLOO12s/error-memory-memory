# error-memory-memory
An automatically running error memory system that can be used with any AI, such as Claude Code or Kimi Code.
第 1 层: Shell 自动捕获 (终端级)
  ↓ source shell_integration.sh → 任何失败命令自动记录
  ↓ 不依赖任何 AI 工具

第 2 层: AI Hook 自动捕获 (AI 工具级)
  ↓ Claude Code: PostToolUse hook 自动触发
  ↓ 其他 AI: 复制 AI_INSTRUCTIONS.md 到对应配置

第 3 层: AI 指令驱动 (对话级)
  ↓ 遇到错误 → 先查询历史 → 解决后记录 → 形成闭环


把 AI_INSTRUCTIONS.md 的内容复制到 你使用的ai工具的 的指令配置/自定义指令设置里即可。

在终端中启用自动捕获
source error-memory-memory/shell_integration.sh

加到 ~/.bashrc 中就永久生效。


自动工作流规则：
规则 1: 遇到错误时 → 先查询历史
规则 2: 解决错误后 → 记录到知识库
规则 3: 已有记录但方案更好 → 更新记录
