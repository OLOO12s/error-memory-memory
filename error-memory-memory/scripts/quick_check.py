#!/usr/bin/env python3
"""
快速检查 - 在解决问题前调用
用法: python quick_check.py "你的问题描述"

这个脚本会在知识库中搜索相关问题，如果找到则显示解决方案，
如果没有找到则提示如何记录新问题。
"""

import sys
from memory_store import get_store


def main():
    if len(sys.argv) < 2:
        print("用法: python quick_check.py \"问题描述\"")
        print("示例: python quick_check.py \"blender渲染黑屏\"")
        return 1
    
    query = sys.argv[1]
    
    # 获取存储
    store = get_store()
    
    # 搜索
    print(f"🔍 正在搜索: \"{query}\"")
    print("-" * 50)
    
    results = store.query(keyword=query, fuzzy=True, limit=5)
    
    if results:
        print(f"✅ 找到 {len(results)} 条相关记录:\n")
        
        for i, entry in enumerate(results, 1):
            print(f"[{i}] [{entry['id']}] {entry['error']}")
            print(f"    场景: {entry.get('context', 'N/A')}")
            print(f"    解决: {entry['solution']}")
            
            if entry.get('cause'):
                print(f"    原因: {entry['cause']}")
            
            # 增加命中计数
            store.update(entry['id'], hit=True)
            
            if i < len(results):
                print()
        
        print("-" * 50)
        print("💡 如果以上方案解决了你的问题，记得更新命中计数:")
        print(f"   python scripts/update_memory.py [ID] --hit")
        
    else:
        print("❌ 未找到相关记录")
        print()
        print("解决完问题后，记得记录下来:")
        print(f"   python scripts/record_memory.py \\")
        print(f"     --error \"{query}\" \\")
        print(f"     --solution \"你的解决方法\" \\")
        print(f"     --tags \"标签1,标签2\"")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
