#!/usr/bin/env python3
"""
全局异常捕获示例
演示如何捕获未处理的异常
"""

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../scripts')

print("=" * 60)
print("自动错误记录系统 - 全局异常捕获示例")
print("=" * 60)

# ============ 启用全局捕获 ============
print("\n启用全局异常捕获...")
print("-" * 40)

from scripts.auto_record_v2 import init, get_manager

# 初始化并启用全局钩子
manager = init(
    enable_global=True,
    auto_tags=["global-hook-example"]
)

print("全局异常捕获已启用！")
print("任何未捕获的异常都会被自动记录。\n")

# ============ 模拟未捕获的异常 ============
print("模拟未捕获的异常场景...")
print("-" * 40)

def function_a():
    """第1层函数"""
    return function_b()

def function_b():
    """第2层函数"""
    return function_c()

def function_c():
    """第3层函数 - 发生错误"""
    # 这里会发生错误
    data = {"key": "value"}
    return data["不存在的键"]

print("\n场景 1: KeyError (多层调用)")
print("  调用链: main -> function_a -> function_b -> function_c")
try:
    function_a()
except KeyError:
    print("  错误被 main 捕获，但已自动记录")

# ============ 模拟另一个错误 ============
print("\n场景 2: 文件操作错误")
def read_settings():
    with open("/path/to/nonexistent/settings.json") as f:
        return f.read()

try:
    read_settings()
except FileNotFoundError:
    print("  文件未找到错误已记录")

# ============ 模拟网络错误 ============
print("\n场景 3: 网络连接错误")
import urllib.error

def fetch_data():
    import urllib.request
    urllib.request.urlopen("http://invalid.domain.example.com", timeout=1)

try:
    fetch_data()
except Exception as e:
    print(f"  网络错误已记录: {type(e).__name__}")

# ============ 模拟计算错误 ============
print("\n场景 4: 计算错误")
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

try:
    calculate_average([])
except ZeroDivisionError:
    print("  除以零错误已记录")

# ============ 模拟类型错误 ============
print("\n场景 5: 类型错误")
def concatenate_strings(a, b):
    return a + b

try:
    concatenate_strings("hello", 123)
except TypeError:
    print("  类型错误已记录")

# ============ 完成 ============
print("\n" + "=" * 60)
print("所有错误已自动记录到知识库！")
print("=" * 60)
print("\n查看记录的错误:")
print("  python ../scripts/list_memory.py --recent 10")
print("  python ../scripts/query_memory.py \"global\" --tag global-hook-example")

# 卸载全局钩子（可选）
print("\n卸载全局异常捕获...")
manager.uninstall_global_hook()
