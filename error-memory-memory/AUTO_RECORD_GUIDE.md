# 自动错误记录系统使用指南

自动记录系统可以在代码运行过程中**自动捕获和记录错误**，无需手动运行 `record_memory.py`。

## 核心特性

- **自动捕获**：使用装饰器或上下文管理器自动捕获异常
- **智能去重**：自动检测重复错误，避免重复记录
- **智能分析**：自动提取标签、生成解决方案建议
- **全局捕获**：可选捕获所有未处理的异常
- **零配置**：导入即可使用，也可通过配置文件自定义

---

## 快速开始

### 方式1：装饰器（推荐）

```python
from scripts.auto_record_v2 import auto_record

@auto_record
def my_function():
    # 如果这里发生异常，会自动记录
    result = 1 / 0
    return result

# 带上下文描述
@auto_record(context="处理用户数据时")
def process_user(user_id):
    user = get_user(user_id)  # 如果出错会自动记录上下文
    return user
```

### 方式2：上下文管理器

```python
from scripts.auto_record_v2 import auto_record_block

with auto_record_block("数据库操作"):
    # 此代码块内的异常会被自动记录
    db.connect()
    db.query("SELECT * FROM users")

# 嵌套使用
with auto_record_block("外层操作"):
    with auto_record_block("内层操作"):
        risky_operation()
```

### 方式3：手动记录

```python
from scripts.auto_record_v2 import get_manager

try:
    risky_operation()
except Exception as e:
    # 手动记录，但仍然享受智能分析
    entry_id = get_manager().record(e, context="自定义上下文")
    print(f"错误已记录: {entry_id}")
```

### 方式4：全局异常捕获（捕获所有未处理异常）

```python
from scripts.auto_record_v2 import init

# 初始化并启用全局捕获
init(enable_global=True)

# 现在任何未捕获的异常都会被自动记录
raise RuntimeError("这个错误会被自动记录")
```

---

## 配置系统

### 配置文件位置

```
.agents/skills/error-memory-memory/config/auto_record.json
```

### 默认配置

```json
{
  "enabled": true,
  "global_hook": false,
  "auto_tags": ["auto-recorded"],
  "skip_patterns": [
    "KeyboardInterrupt",
    "SystemExit"
  ],
  "deduplication": {
    "enabled": true,
    "time_window_minutes": 60
  },
  "output": {
    "print_on_record": true,
    "show_traceback_preview": true
  }
}
```

### 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `enabled` | 是否启用自动记录 | `true` |
| `global_hook` | 是否捕获全局未处理异常 | `false` |
| `auto_tags` | 自动添加的标签 | `["auto-recorded"]` |
| `skip_patterns` | 跳过的错误模式（正则） | 见上方 |
| `deduplication.enabled` | 是否启用去重 | `true` |
| `deduplication.time_window_minutes` | 去重时间窗口（分钟） | `60` |
| `output.print_on_record` | 记录时是否打印信息 | `true` |

### 程序化配置

```python
from auto_record_config import get_config

config = get_config()

# 添加自动标签
config.add_auto_tag("my-project")

# 添加跳过模式
config.add_skip_pattern("test_.*")

# 修改配置项
config.set("deduplication.time_window_minutes", 30)

# 查看当前配置
config.show()

# 重置为默认
config.reset()
```

---

## 智能功能详解

### 1. 智能去重

系统会自动检测重复错误，避免在短时间内重复记录相同的错误。

```python
# 第一次会记录
@auto_record
def func():
    raise ValueError("same error")

# 短时间内再次调用，不会重复记录
try:
    func()
except:
    pass
try:
    func()  # 这条不会记录
except:
    pass
```

### 2. 智能解决方案

根据错误类型自动生成解决方案：

| 错误类型 | 自动生成的解决方案 |
|----------|-------------------|
| `ModuleNotFoundError` | `pip install {模块名}` |
| `FileNotFoundError` | 检查文件路径 |
| `KeyError` | 检查字典键是否存在 |
| `IndexError` | 检查索引是否越界 |
| `AttributeError` | 检查对象属性 |
| `ConnectionError` | 检查网络连接 |

### 3. 智能标签提取

自动从错误中提取标签：
- 错误类型标签（如 `import`, `file`, `network`）
- 模块名标签
- 自定义标签

---

## 高级用法

### 自定义错误解决方案

```python
from auto_record_config import get_config

config = get_config()

# 添加自定义错误解决方案
config.config["error_solutions"]["MyCustomError"] = {
    "solution": "自定义解决方案: 检查 {param}",
    "auto_extract": True,
    "extract_pattern": "param='([^']+)'"
}
config._save()
```

### 在项目中全局启用

创建 `auto_record_init.py`：

```python
# 在项目根目录创建此文件，在程序入口导入
from scripts.auto_record_v2 import init

# 初始化自动记录
init(
    enable_global=True,  # 捕获所有未处理异常
    auto_tags=["my-project", "production"]  # 自动标签
)

print("自动错误记录已启用")
```

在主程序入口：

```python
# main.py
import auto_record_init  # 放在最前面

# 你的代码...
```

### 与现有代码集成

```python
# 批量处理时记录每个错误
from scripts.auto_record_v2 import auto_record_block

def process_batch(items):
    results = []
    for item in items:
        try:
            with auto_record_block(f"处理 item {item['id']}"):
                result = process_item(item)
                results.append(result)
        except Exception:
            continue  # 继续处理下一个
    return results
```

### 选择性禁用

```python
from scripts.auto_record_v2 import get_manager

# 临时禁用
manager = get_manager()
manager.disable()

# 执行不需要记录的代码
...

# 重新启用
manager.enable()
```

---

## 实际示例

### Web 应用集成

```python
from flask import Flask
from scripts.auto_record_v2 import auto_record, init

app = Flask(__name__)
init(enable_global=True, auto_tags=["web", "flask"])

@app.route('/api/users/<id>')
@auto_record(context="API: 获取用户信息")
def get_user(id):
    user = db.query(User).get(id)
    if not user:
        raise ValueError(f"User {id} not found")
    return jsonify(user.to_dict())
```

### 数据处理管道

```python
from scripts.auto_record_v2 import auto_record, auto_record_block

class DataPipeline:
    @auto_record(context="数据清洗")
    def clean(self, data):
        return clean_data(data)
    
    @auto_record(context="数据转换")
    def transform(self, data):
        return transform_data(data)
    
    def run(self, data):
        with auto_record_block("执行完整管道"):
            cleaned = self.clean(data)
            transformed = self.transform(cleaned)
            return transformed
```

### 脚本自动化

```python
#!/usr/bin/env python3
from scripts.auto_record_v2 import init, auto_record

# 脚本开头初始化
init(enable_global=True, auto_tags=["script", "daily-task"])

@auto_record(context="每日数据同步")
def daily_sync():
    download_data()
    process_data()
    upload_results()

if __name__ == "__main__":
    daily_sync()
```

---

## 查询自动记录的错误

```bash
# 查看所有自动记录的错误
python scripts/list_memory.py --tag auto-recorded

# 查看最近的10条
python scripts/list_memory.py --recent 10

# 搜索特定错误
python scripts/query_memory.py "ValueError" --fuzzy
```

---

## 故障排除

### 问题：自动记录没有生效

**检查清单：**
1. 确认 `enabled` 配置为 `true`
2. 检查错误是否匹配 `skip_patterns`
3. 确认去重时间窗口内没有重复记录

### 问题：记录太多重复错误

**解决方案：**
```python
# 缩短去重时间窗口
config.set("deduplication.time_window_minutes", 5)

# 或添加更多跳过模式
config.add_skip_pattern("test_.*")
```

### 问题：不想要某些错误被记录

**解决方案：**
```python
# 添加跳过模式
config.add_skip_pattern("SomeSpecificError")

# 或在代码中处理
@auto_record
def func():
    try:
        # 可能出错但不希望记录的代码
        pass
    except SomeSpecificError:
        pass  # 静默处理
```

---

## 最佳实践

1. **项目开始时初始化**：在项目入口启用自动记录
2. **使用描述性上下文**：让记录更有价值
3. **定期检查知识库**：每周回顾记录的错误
4. **更新解决方案**：发现更好的解决方法时更新记录
5. **合理设置去重**：避免记录过多重复错误

---

> 💡 **提示**：自动记录是辅助工具，不要完全依赖它。遇到复杂问题时，仍然需要手动分析和记录详细信息。
