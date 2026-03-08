# 错误记忆与解决系统

一个智能的个人知识库系统，用于记录、管理和复用问题解决经验。

## 核心功能

### 1. 手动记录（传统方式）
```bash
# 记录新错误
python scripts/record_memory.py \
    --error "错误描述" \
    --solution "解决方法" \
    --tags "标签1,标签2"
```

### 2. 自动记录（新功能！）
无需手动运行命令，代码中的错误会自动捕获和记录。

```python
from scripts.auto_record_v2 import auto_record, init

# 初始化
init(enable_global=True)

# 使用装饰器
@auto_record(context="处理数据时")
def my_function():
    # 发生错误会自动记录
    result = 1 / 0
```

## 快速开始

### 安装
无需安装，直接使用。

### 1分钟上手

```bash
# 进入 skill 目录
cd .agents/skills/error-memory-memory

# 运行快速测试
python quick_start.py

# 查看记录的错误
python scripts/list_memory.py
```

## 使用方式对比

| 方式 | 使用场景 | 代码示例 |
|------|----------|----------|
| **手动记录** | 已解决的问题，需要详细记录 | `record_memory.py --error "..."` |
| **装饰器** | 特定函数的错误监控 | `@auto_record` |
| **上下文管理器** | 代码块错误监控 | `with auto_record_block():` |
| **全局捕获** | 捕获所有未处理异常 | `init(enable_global=True)` |

## 文件结构

```
error-memory-memory/
├── SKILL.md                      # 完整使用文档
├── README.md                     # 本文件
├── AUTO_RECORD_GUIDE.md          # 自动记录详细指南
├── quick_start.py                # 快速测试脚本
├── config/                       # 配置文件
│   └── auto_record.json         # 自动记录配置
├── memory/                       # 错误记录存储
│   ├── index.json               # 索引
│   └── ERR-XXX.json             # 单条记录
├── scripts/                      # 工具脚本
│   ├── auto_record_v2.py        # 自动记录核心
│   ├── auto_record_config.py    # 配置管理
│   ├── record_memory.py         # 手动记录
│   ├── query_memory.py          # 查询记录
│   ├── list_memory.py           # 列出记录
│   └── stats_memory.py          # 统计分析
└── examples/                     # 示例代码
    ├── basic_example.py         # 基础示例
    ├── advanced_example.py      # 高级示例
    ├── global_hook_example.py   # 全局捕获示例
    └── project_integration_demo.py  # 项目集成示例
```

## 常用命令

```bash
# 查询历史记录
python scripts/query_memory.py "关键词" --fuzzy

# 列出所有记录
python scripts/list_memory.py

# 按标签筛选
python scripts/list_memory.py --tag "python"

# 统计信息
python scripts/stats_memory.py

# 运行示例
python examples/basic_example.py
python examples/advanced_example.py
```

## 智能特性

### 自动去重
相同错误在短时间内不会重复记录，避免知识库膨胀。

### 智能标签
自动从错误中提取标签：
- 错误类型标签（`import`, `file`, `network`）
- 模块名标签
- 自定义标签

### 智能解决方案
根据错误类型自动生成解决方案：
- `ModuleNotFoundError` → `pip install {模块名}`
- `FileNotFoundError` → 检查文件路径
- `KeyError` → 检查字典键
- 等等...

## 配置

配置文件：`config/auto_record.json`

```json
{
  "enabled": true,
  "auto_tags": ["auto-recorded"],
  "skip_patterns": ["KeyboardInterrupt"],
  "deduplication": {
    "enabled": true,
    "time_window_minutes": 60
  }
}
```

## 项目集成示例

在 Python 项目入口文件（如 `main.py`）添加：

```python
# main.py
from scripts.auto_record_v2 import init

# 初始化自动记录
init(
    enable_global=True,
    auto_tags=["my-project", "production"]
)

# 你的代码...
```

更多示例见 `examples/` 目录。

## 工作流程

```
遇到问题
    ↓
自动捕获 → 记录到知识库
    ↓
定期回顾 → 积累经验
    ↓
下次遇到 → 查询历史 → 直接应用解决方案
```

## 核心理念

> **不要重复踩同一个坑**

每次遇到问题并解决后，系统会自动或手动记录下来。下次遇到类似问题时，先查知识库，直接应用已验证的解决方案，而不是重新试错。

## 更多信息

- [完整使用文档](SKILL.md)
- [自动记录指南](AUTO_RECORD_GUIDE.md)
- [基础示例](examples/basic_example.py)
- [高级示例](examples/advanced_example.py)

---

**记住**：这个系统的价值在于复用。记录越多，查询越多，节省的时间就越多。
