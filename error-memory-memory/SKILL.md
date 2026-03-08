---
name: error-memory-memory
description: 错误记忆与解决系统。自动记录运算过程中遇到的问题和解决办法，建立个人知识库。核心功能是记录错误、查询历史解决方案、避免重复试错，实现经验的积累和复用。
---

# 错误记忆与解决系统 (Error Memory System)

一个用于记录、管理和复用问题解决经验的 **AI 通用** 知识库系统。

## 核心理念

> **不要重复踩同一个坑**

## 自动运行机制（三层架构）

系统通过三层架构实现自动运行，不依赖特定 AI 工具：

### 第 1 层: Shell 自动捕获（终端级）

在 `.bashrc` 中添加一行即可启用：

```bash
source F:/KCODE/.agents/skills/error-memory-memory/shell_integration.sh
```

启用后，终端中所有失败的命令都会自动记录到知识库。

提供便捷命令:
- `em-query "关键词"` — 查询历史错误
- `em-record -e "错误" -s "方案"` — 记录错误
- `em-list` — 列出所有记录
- `em-stats` — 统计信息
- `errmem python script.py` — 包装命令，捕获完整错误输出

### 第 2 层: AI Hook 自动捕获（AI 工具级）

#### Claude Code（已配置）

通过 `PostToolUse` hook 自动捕获 Bash 和 MCP 工具的错误：

```json
// .claude/settings.local.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py hook-stdin"
        }]
      }
    ]
  }
}
```

#### Kimi Code / 其他 AI 工具

将 `AI_INSTRUCTIONS.md` 的内容复制到对应 AI 工具的指令配置中：
- Kimi Code: 项目设置/自定义指令
- Cursor: `.cursorrules` 文件
- Windsurf: `.windsurfrules` 文件
- 其他: 查找该工具的 "system prompt" 或 "project instructions" 配置

### 第 3 层: AI 指令驱动（对话级）

通过指令文件告诉 AI 在对话中自动执行错误记录流程：

1. **遇到错误时** → 先查询历史
2. **解决错误后** → 记录到知识库
3. **发现更好方案** → 更新历史记录

---

## 通用 CLI 工具

`error_mem_cli.py` 是系统的统一入口，可从任何位置调用：

```bash
# 查询历史错误
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py query "关键词"

# 记录新错误
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py record \
    -e "错误描述" -s "解决方法" -t "标签"

# 列出所有记录
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py list --recent 10

# 更新记录
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py update ERR-001 -s "更好方案"

# 统计
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py stats

# 包装命令执行（自动捕获错误）
python F:/KCODE/.agents/skills/error-memory-memory/error_mem_cli.py exec -- python script.py

# AI Hook 处理器（从 stdin 读取 JSON）
echo '{"tool_name":"Bash",...}' | python error_mem_cli.py hook-stdin
```

---

## 记录结构

每条错误记录包含以下字段：

| 字段 | 说明 | 必填 |
|------|------|------|
| `id` | 唯一编号 (ERR-XXX) | 自动生成 |
| `error` | 错误描述/症状 | 是 |
| `context` | 发生场景/环境 | 建议 |
| `solution` | 解决方法 | 是 |
| `tags` | 标签，逗号分隔 | 建议 |
| `cause` | 根本原因分析 | 可选 |
| `prevention` | 预防措施 | 可选 |
| `created_at` | 创建时间 | 自动生成 |
| `updated_at` | 更新时间 | 自动更新 |
| `hit_count` | 被查询命中次数 | 自动统计 |

## 智能特性

### 自动去重
相同错误在 1 小时内不会重复记录（可配置）。

### 噪音过滤
自动跳过非真正错误的命令失败（如 `grep` 无匹配、`test` 条件不满足等）。

### 智能解决方案
根据错误类型自动生成解决方案建议：
- `ModuleNotFoundError` → `pip install {模块名}`
- `FileNotFoundError` → 检查文件路径
- `KeyError` → 使用 `.get()` 方法
- 等等...

### 历史方案推荐
记录新错误时，自动查询类似历史错误并推荐已验证的解决方案。

---

## Python 集成（可选）

除了 CLI 和 Shell 集成，也支持在 Python 代码中直接使用：

### 装饰器

```python
from scripts.auto_record_v2 import auto_record

@auto_record(context="处理数据时")
def process_data(data):
    return transform(data)
```

### 上下文管理器

```python
from scripts.auto_record_v2 import auto_record_block

with auto_record_block("数据库操作"):
    db.connect()
    db.query("SELECT * FROM users")
```

### 全局捕获

```python
from scripts.auto_record_v2 import init
init(enable_global=True, auto_tags=["my-project"])
```

---

## 配置

配置文件: `config/auto_record.json`

```json
{
  "enabled": true,
  "auto_tags": ["auto-recorded"],
  "skip_patterns": ["KeyboardInterrupt", "SystemExit"],
  "deduplication": {
    "enabled": true,
    "time_window_minutes": 60
  }
}
```

## 标签规范

| 类别 | 标签示例 |
|------|----------|
| 语言/工具 | `python`, `blender`, `docker`, `git` |
| 错误类型 | `import`, `file`, `network`, `syntax`, `type` |
| 场景 | `api`, `cli`, `render`, `build`, `deploy` |
| 来源 | `auto-captured`, `manual`, `shell`, `mcp` |

## 文件结构

```
error-memory-memory/
├── error_mem_cli.py              # 通用 CLI 入口（主工具）
├── shell_integration.sh          # Bash 自动捕获集成
├── AI_INSTRUCTIONS.md            # AI 通用指令（复制到任何 AI 工具）
├── SKILL.md                      # 本文件
├── README.md                     # 简要说明
├── config/
│   └── auto_record.json          # 配置文件
├── memory/                       # 错误记录存储
│   ├── index.json
│   └── ERR-XXX.json
├── scripts/                      # 核心模块
│   ├── memory_store.py           # 存储引擎
│   ├── auto_record_config.py     # 配置管理
│   ├── auto_record_v2.py         # Python 集成
│   ├── record_memory.py          # 手动记录脚本
│   ├── query_memory.py           # 查询脚本
│   └── list_memory.py            # 列表脚本
└── examples/                     # 示例代码
```

## 存储位置

```
.agents/skills/error-memory-memory/memory/
├── index.json          # 索引文件
├── .recent_hashes.json # 去重哈希缓存
├── ERR-001.json        # 单条记录
└── ...
```

---

> **记住**：这个系统的价值在于复用。记录越多，查询越多，节省的时间就越多。
