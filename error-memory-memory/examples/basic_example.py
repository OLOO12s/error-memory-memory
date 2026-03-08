#!/usr/bin/env python3
"""
自动错误记录基础示例
演示各种使用方式
"""

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../scripts')

from scripts.auto_record_v2 import auto_record, auto_record_block, get_manager

print("=" * 60)
print("自动错误记录系统 - 基础示例")
print("=" * 60)

# ============ 示例 1: 装饰器基础用法 ============
print("\n示例 1: 装饰器基础用法")
print("-" * 40)

@auto_record
def divide_by_zero():
    """这个函数会触发 ZeroDivisionError"""
    return 1 / 0

try:
    divide_by_zero()
except ZeroDivisionError:
    print("错误已捕获并记录")

# ============ 示例 2: 带上下文的装饰器 ============
print("\n示例 2: 带上下文的装饰器")
print("-" * 40)

@auto_record(context="处理订单数据时")
def process_order(order_id):
    """模拟处理订单"""
    if order_id < 0:
        raise ValueError(f"无效的订单ID: {order_id}")
    return {"id": order_id, "status": "processed"}

try:
    process_order(-1)
except ValueError:
    print("订单处理错误已记录")

# ============ 示例 3: 上下文管理器 ============
print("\n示例 3: 上下文管理器")
print("-" * 40)

try:
    with auto_record_block("数据库查询操作"):
        # 模拟数据库操作
        connection = None
        connection.execute("SELECT * FROM users")  # 这里会报错
except AttributeError:
    print("数据库操作错误已记录")

# ============ 示例 4: 文件操作 ============
print("\n示例 4: 文件操作错误")
print("-" * 40)

@auto_record(context="读取配置文件")
def read_config(filename):
    with open(filename, 'r') as f:
        return f.read()

try:
    read_config("不存在的文件.txt")
except FileNotFoundError:
    print("文件未找到错误已记录")

# ============ 示例 5: 嵌套使用 ============
print("\n示例 5: 嵌套使用")
print("-" * 40)

@auto_record(context="外层函数")
def outer_function():
    with auto_record_block("内层代码块"):
        data = {"key": "value"}
        return data["不存在的键"]  # KeyError

try:
    outer_function()
except KeyError:
    print("嵌套错误已记录")

# ============ 示例 6: 模块导入错误 ============
print("\n示例 6: 模块导入错误")
print("-" * 40)

@auto_record(context="加载第三方库")
def load_external_lib():
    import some_nonexistent_module
    return some_nonexistent_lib

try:
    load_external_lib()
except ModuleNotFoundError:
    print("模块导入错误已记录")

# ============ 示例 7: 网络操作模拟 ============
print("\n示例 7: 网络操作")
print("-" * 40)

@auto_record(context="API 调用")
def call_api():
    import urllib.request
    # 尝试访问一个可能失败的地址
    urllib.request.urlopen("http://localhost:99999")

try:
    call_api()
except Exception as e:
    print(f"网络错误已记录: {type(e).__name__}")

# ============ 示例 8: 重复错误检测 ============
print("\n示例 8: 重复错误检测（第二次不会记录）")
print("-" * 40)

@auto_record
def same_error():
    raise ValueError("同样的错误")

try:
    same_error()
    print("第一次错误已记录")
except:
    pass

try:
    same_error()
    print("第二次错误（应跳过）")
except:
    pass

# ============ 完成 ============
print("\n" + "=" * 60)
print("示例运行完成！")
print("=" * 60)
print("\n查看记录的错误:")
print("  cd .. && python scripts/list_memory.py --recent 10")
