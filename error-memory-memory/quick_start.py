#!/usr/bin/env python3
"""
自动错误记录系统 - 快速启动
一键测试自动记录功能
"""

import sys
from pathlib import Path

# 添加脚本路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from auto_record_v2 import init, auto_record, auto_record_block
from memory_store import get_store

def main():
    print("=" * 60)
    print("错误记忆系统 - 自动记录快速测试")
    print("=" * 60)
    
    # 初始化
    print("\n1. 初始化自动记录系统...")
    init(enable_global=False, auto_tags=["quick-test"])
    print("   初始化完成！")
    
    # 测试装饰器
    print("\n2. 测试装饰器...")
    
    @auto_record(context="除法运算")
    def divide(a, b):
        return a / b
    
    try:
        divide(10, 0)
    except:
        print("   除零错误已自动记录")
    
    # 测试上下文管理器
    print("\n3. 测试上下文管理器...")
    
    try:
        with auto_record_block("字典访问"):
            data = {}
            value = data["不存在的键"]
    except:
        print("   KeyError 已自动记录")
    
    # 测试文件错误
    print("\n4. 测试文件操作...")
    
    @auto_record(context="读取文件")
    def read_file(path):
        with open(path) as f:
            return f.read()
    
    try:
        read_file("/不存在的路径/文件.txt")
    except:
        print("   文件未找到错误已自动记录")
    
    # 测试导入错误
    print("\n5. 测试导入错误...")
    
    @auto_record(context="导入模块")
    def import_module():
        import 不存在的模块
    
    try:
        import_module()
    except:
        print("   模块导入错误已自动记录")
    
    # 显示统计
    print("\n" + "=" * 60)
    print("6. 记录统计")
    print("=" * 60)
    
    store = get_store()
    stats = store.get_stats()
    
    print(f"\n   总记录数: {stats['total_entries']}")
    print(f"   总标签数: {stats['total_tags']}")
    print(f"   标签分布: {stats['tag_distribution']}")
    
    # 显示最近的记录
    print("\n   最近的自动记录:")
    entries = store.list_all(recent=5)
    for entry in entries:
        print(f"   - [{entry['id']}] {entry['error'][:50]}...")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n查看所有记录:")
    print("  python scripts/list_memory.py")
    print("\n搜索记录:")
    print("  python scripts/query_memory.py \"除零\" --fuzzy")
    print("\n查看统计:")
    print("  python scripts/stats_memory.py")

if __name__ == "__main__":
    main()
