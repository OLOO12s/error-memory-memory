#!/usr/bin/env python3
"""
自动错误记录高级示例
演示全局捕获、配置自定义等高级功能
"""

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../scripts')

from scripts.auto_record_v2 import init, auto_record, get_manager
from scripts.auto_record_config import get_config

print("=" * 60)
print("自动错误记录系统 - 高级示例")
print("=" * 60)

# ============ 示例 1: 初始化配置 ============
print("\n示例 1: 初始化自动记录")
print("-" * 40)

# 初始化（不启用全局钩子，我们会手动演示）
manager = init(
    enable_global=False,
    auto_tags=["advanced-example", "demo"]
)

print(f"自动记录状态: {'启用' if manager.is_enabled() else '禁用'}")

# ============ 示例 2: 自定义配置 ============
print("\n示例 2: 自定义配置")
print("-" * 40)

config = get_config()

# 添加项目标签
config.add_auto_tag("my-project-v2")

# 添加自定义跳过模式
config.add_skip_pattern("调试错误")

# 缩短去重时间窗口
config.set("deduplication.time_window_minutes", 5)

print("配置已更新")
print(f"自动标签: {config.get_auto_tags()}")

# ============ 示例 3: 数据处理管道 ============
print("\n示例 3: 数据处理管道")
print("-" * 40)

class DataPipeline:
    """数据处理管道，每个阶段都有错误记录"""
    
    @auto_record(context="数据验证阶段")
    def validate(self, data):
        if not isinstance(data, dict):
            raise TypeError("数据必须是字典类型")
        if "id" not in data:
            raise KeyError("数据缺少 'id' 字段")
        return True
    
    @auto_record(context="数据清洗阶段")
    def clean(self, data):
        # 模拟清洗错误
        if data.get("status") == "invalid":
            raise ValueError("无效的数据状态")
        return {k: v.strip() if isinstance(v, str) else v 
                for k, v in data.items()}
    
    @auto_record(context="数据转换阶段")
    def transform(self, data):
        # 模拟转换错误
        try:
            data["amount"] = float(data["amount"])
        except (KeyError, ValueError) as e:
            raise ValueError(f"金额转换失败: {e}")
        return data
    
    def process(self, data):
        """执行完整管道"""
        print(f"  处理数据: {data}")
        self.validate(data)
        cleaned = self.clean(data)
        transformed = self.transform(cleaned)
        return transformed

pipeline = DataPipeline()

# 测试各种错误场景
test_cases = [
    {"id": 1, "status": "valid", "amount": "100.50"},  # 正常
    "不是字典",  # TypeError
    {"status": "valid"},  # KeyError
    {"id": 2, "status": "invalid", "amount": "100"},  # ValueError
    {"id": 3, "status": "valid", "amount": "abc"},  # 转换错误
]

for i, test_data in enumerate(test_cases):
    print(f"\n  测试用例 {i+1}:")
    try:
        result = pipeline.process(test_data)
        print(f"  成功: {result}")
    except Exception as e:
        print(f"  失败: {type(e).__name__}")

# ============ 示例 4: 批量操作错误处理 ============
print("\n示例 4: 批量操作错误处理")
print("-" * 40)

@auto_record(context="批量处理项目")
def batch_process(items):
    results = []
    errors = []
    
    for i, item in enumerate(items):
        try:
            # 模拟处理
            if item == "error":
                raise ValueError(f"项目 {i} 处理失败")
            results.append(f"processed_{item}")
        except Exception as e:
            errors.append((i, str(e)))
            continue  # 继续处理下一个
    
    return results, errors

items = ["a", "b", "error", "c", "error", "d"]
results, errors = batch_process(items)

print(f"  成功: {len(results)} 项")
print(f"  失败: {len(errors)} 项")

# ============ 示例 5: API 调用模拟 ============
print("\n示例 5: API 调用模拟")
print("-" * 40)

import random

@auto_record(context="外部 API 调用")
def call_external_api(endpoint, params=None):
    """模拟 API 调用"""
    # 模拟随机错误
    error_types = [
        None,
        ConnectionError("连接超时"),
        TimeoutError("请求超时"),
        ValueError("无效的响应格式"),
        None,
    ]
    
    error = random.choice(error_types)
    if error:
        raise error
    
    return {"status": "success", "data": []}

# 模拟多次调用
for i in range(3):
    try:
        result = call_external_api(f"/api/users/{i}")
        print(f"  调用 {i+1}: 成功")
    except Exception as e:
        print(f"  调用 {i+1}: {type(e).__name__}")

# ============ 示例 6: 临时禁用记录 ============
print("\n示例 6: 临时禁用记录")
print("-" * 40)

@auto_record
def noisy_function():
    raise RuntimeError("这个错误不应该被记录")

print("  禁用自动记录...")
manager.disable()

try:
    noisy_function()
except:
    print("  错误发生但没有记录")

print("  重新启用自动记录...")
manager.enable()

# ============ 示例 7: 查看当前配置 ============
print("\n示例 7: 当前配置")
print("-" * 40)

print("当前配置摘要:")
print(f"  启用状态: {config.is_enabled()}")
print(f"  全局钩子: {config.get('global_hook')}")
print(f"  自动标签: {config.get_auto_tags()}")
print(f"  跳过模式: {len(config.get('skip_patterns', []))} 个")
print(f"  去重窗口: {config.get('deduplication.time_window_minutes')} 分钟")

# ============ 完成 ============
print("\n" + "=" * 60)
print("高级示例运行完成！")
print("=" * 60)
print("\n查询记录的错误:")
print("  cd .. && python scripts/query_memory.py \"advanced\" --fuzzy")
print("  cd .. && python scripts/stats_memory.py")
