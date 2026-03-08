#!/usr/bin/env python3
"""
项目集成演示
展示如何在实际项目中集成自动错误记录
"""

import sys
import os
sys.path.insert(0, '..')
sys.path.insert(0, '../scripts')

# ============ 项目入口文件示例 ============
# 在实际项目中，将以下内容放在 main.py 或 app.py 的开头

print("=" * 60)
print("项目集成演示 - 模拟一个数据处理应用")
print("=" * 60)

# ---- 步骤 1: 初始化自动记录 ----
print("\n[初始化] 启动自动错误记录系统...")

from scripts.auto_record_v2 import init, auto_record, auto_record_block
from scripts.auto_record_config import get_config

# 初始化
init(
    enable_global=True,  # 捕获所有未处理的异常
    auto_tags=["data-processor", "v1.0"]  # 项目标签
)

# 自定义配置
config = get_config()
config.add_auto_tag(os.environ.get("ENV", "development"))
config.set("output.print_on_record", True)

print("[初始化] 完成！")

# ============ 模拟应用代码 ============

class Database:
    """模拟数据库"""
    
    def __init__(self):
        self.connected = False
    
    @auto_record(context="数据库连接")
    def connect(self, connection_string):
        if "invalid" in connection_string:
            raise ConnectionError(f"无法连接到数据库: {connection_string}")
        self.connected = True
        print(f"  数据库已连接: {connection_string}")
    
    @auto_record(context="数据库查询")
    def query(self, sql):
        if not self.connected:
            raise RuntimeError("数据库未连接")
        if "DROP" in sql.upper():
            raise PermissionError("不允许执行删除操作")
        return [{"id": 1, "name": "测试数据"}]
    
    def close(self):
        self.connected = False

class DataValidator:
    """数据验证器"""
    
    @auto_record(context="数据验证")
    def validate(self, data, schema):
        for field, field_type in schema.items():
            if field not in data:
                raise KeyError(f"缺少必填字段: {field}")
            if not isinstance(data[field], field_type):
                raise TypeError(f"字段 {field} 类型错误，期望 {field_type}")
        return True

class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.db = Database()
        self.validator = DataValidator()
    
    @auto_record(context="初始化处理器")
    def setup(self, config):
        self.db.connect(config.get("db_url", "default"))
    
    @auto_record(context="处理单个记录")
    def process_record(self, record, schema):
        # 验证
        self.validator.validate(record, schema)
        
        # 处理
        with auto_record_block("数据库操作"):
            existing = self.db.query(f"SELECT * FROM items WHERE id = {record['id']}")
            if existing:
                # 更新
                pass
            else:
                # 插入
                pass
        
        return {"status": "success", "id": record['id']}
    
    @auto_record(context="批量处理")
    def process_batch(self, records, schema):
        results = []
        errors = []
        
        for i, record in enumerate(records):
            try:
                result = self.process_record(record, schema)
                results.append(result)
            except Exception as e:
                errors.append({"index": i, "error": str(e)})
                # 错误已被自动记录
                continue
        
        return {
            "success": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    def cleanup(self):
        self.db.close()

# ============ 运行演示 ============

print("\n[应用] 创建数据处理器...")
processor = DataProcessor()

# 测试场景 1: 正常操作
print("\n[场景 1] 正常操作")
print("-" * 40)
try:
    processor.setup({"db_url": "postgresql://localhost/db"})
    
    schema = {"id": int, "name": str, "value": float}
    records = [
        {"id": 1, "name": "Item 1", "value": 100.0},
        {"id": 2, "name": "Item 2", "value": 200.0},
    ]
    
    result = processor.process_batch(records, schema)
    print(f"处理完成: {result['success']} 成功, {result['failed']} 失败")
    processor.cleanup()
except Exception as e:
    print(f"错误: {e}")

# 测试场景 2: 数据库连接错误
print("\n[场景 2] 数据库连接错误")
print("-" * 40)
try:
    processor2 = DataProcessor()
    processor2.setup({"db_url": "invalid://connection"})
except Exception as e:
    print(f"预期错误: {type(e).__name__} (已自动记录)")

# 测试场景 3: 数据验证错误
print("\n[场景 3] 数据验证错误")
print("-" * 40)
try:
    processor3 = DataProcessor()
    processor3.setup({"db_url": "postgresql://localhost/db"})
    
    schema = {"id": int, "name": str}
    bad_records = [
        {"id": 1, "name": "Good"},
        {"id": "not-int", "name": "Bad ID"},  # 类型错误
        {"name": "Missing ID"},  # 缺少字段
    ]
    
    result = processor3.process_batch(bad_records, schema)
    print(f"处理完成: {result['success']} 成功, {result['failed']} 失败")
    processor3.cleanup()
except Exception as e:
    print(f"错误: {e}")

# 测试场景 4: 权限错误
print("\n[场景 4] 权限错误")
print("-" * 40)
try:
    processor4 = DataProcessor()
    processor4.setup({"db_url": "postgresql://localhost/db"})
    processor4.db.query("DROP TABLE users")  # 危险操作
except Exception as e:
    print(f"预期错误: {type(e).__name__} (已自动记录)")
    processor4.cleanup()

# ============ 汇总 ============
print("\n" + "=" * 60)
print("演示完成！")
print("=" * 60)

print("\n[统计] 自动记录的错误:")
from scripts.memory_store import get_store
store = get_store()
stats = store.get_stats()

print(f"  总记录数: {stats['total_entries']}")
print(f"  总标签数: {stats['total_tags']}")
print(f"  查询命中: {stats['total_hits']} 次")

print("\n[建议] 查看记录:")
print("  cd .. && python scripts/stats_memory.py")
print("  cd .. && python scripts/list_memory.py --recent 10")
print("  cd .. && python scripts/query_memory.py \"data\" --tag data-processor")

print("\n[提示] 在生产环境中，自动记录的错误会帮助你:")
print("  1. 快速定位问题发生的代码位置")
print("  2. 了解最常见的错误类型")
print("  3. 积累解决方案，避免重复踩坑")
