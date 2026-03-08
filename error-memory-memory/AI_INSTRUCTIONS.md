# 错误记忆系统 - AI 自动工作流指令

> **本文件是给 AI 编程助手阅读的通用指令。**
> 适用于: Claude Code, Kimi Code, Cursor, Copilot, 或任何 AI 编程工具。
> 将本文件内容复制到你使用的 AI 工具的指令配置中即可。

## CLI 工具位置

```
F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py
```

简写变量（在指令中使用）:
```
ERRMEM="python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py"
```

---

## 自动工作流（必须遵循）

### 规则 1: 遇到错误时 → 先查询历史

当你执行命令或代码遇到错误时，**在尝试修复之前**，先查询错误知识库：

```bash
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py query "错误关键词"
```

如果找到历史解决方案，优先使用已验证的方案。

### 规则 2: 解决错误后 → 记录到知识库

成功修复一个错误后，**立即记录**解决方案：

```bash
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py record \
    -e "错误的完整描述" \
    -s "你使用的解决方法" \
    -c "错误发生的场景和上下文" \
    -t "相关标签,逗号分隔"
```

### 规则 3: 已有记录但方案更好 → 更新记录

如果你发现了比历史记录更好的解决方案，更新它：

```bash
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py update ERR-XXX \
    -s "更好的解决方案"
```

---

## 命令速查

| 操作 | 命令 |
|------|------|
| 查询 | `python error_mem_cli.py query "关键词"` |
| 记录 | `python error_mem_cli.py record -e "错误" -s "方案" -t "标签"` |
| 列表 | `python error_mem_cli.py list --recent 10` |
| 更新 | `python error_mem_cli.py update ERR-001 -s "新方案"` |
| 统计 | `python error_mem_cli.py stats` |

---

## 标签规范

记录时请使用统一的标签体系:

- **语言/工具**: `python`, `javascript`, `blender`, `docker`, `git`
- **错误类型**: `import`, `file`, `network`, `syntax`, `type`, `permission`
- **场景**: `api`, `cli`, `render`, `build`, `deploy`
- **来源**: `auto-captured` (自动捕获), `manual` (手动记录)

---

## 不需要记录的情况

- 拼写错误、简单打字错误
- 用户主动取消的操作 (KeyboardInterrupt)
- 测试中预期的失败
- 一次性的临时调试命令
