#!/usr/bin/env python3
"""
更新错误记录
用法: python update_memory.py ERR-001 [--solution "..."] [--add-tags "..."] [--hit]
"""

import argparse
import sys
from memory_store import get_store


def main():
    parser = argparse.ArgumentParser(
        description="更新现有错误记录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 更新解决方案
  python update_memory.py ERR-001 --solution "更好的解决方法"
  
  # 添加标签
  python update_memory.py ERR-001 --add-tags "blender,render"
  
  # 增加命中计数（表示又用到了这条记录）
  python update_memory.py ERR-001 --hit
  
  # 组合操作
  python update_memory.py ERR-001 --hit --add-tags "常用"
        """
    )
    
    parser.add_argument("entry_id",
                        help="记录ID（如 ERR-001）")
    parser.add_argument("--solution", "-s",
                        help="更新解决方法")
    parser.add_argument("--context", "-c",
                        help="更新场景描述")
    parser.add_argument("--cause",
                        help="更新根本原因")
    parser.add_argument("--prevention", "-p",
                        help="更新预防措施")
    parser.add_argument("--add-tags", "-t",
                        help="添加标签（逗号分隔）")
    parser.add_argument("--hit", action="store_true",
                        help="增加命中计数")
    
    args = parser.parse_args()
    
    # 获取存储
    store = get_store()
    
    # 检查记录是否存在
    entry = store.get(args.entry_id)
    if not entry:
        print(f"错误: 记录 {args.entry_id} 不存在")
        return 1
    
    # 构建更新参数
    update_kwargs = {}
    
    if args.solution:
        update_kwargs["solution"] = args.solution
    if args.context:
        update_kwargs["context"] = args.context
    if args.cause:
        update_kwargs["cause"] = args.cause
    if args.prevention:
        update_kwargs["prevention"] = args.prevention
    if args.add_tags:
        update_kwargs["add_tags"] = args.add_tags
    if args.hit:
        update_kwargs["hit"] = True
    
    if not update_kwargs:
        print("警告: 没有提供任何更新内容")
        print(f"使用 --help 查看可用选项")
        return 1
    
    # 执行更新
    success = store.update(args.entry_id, **update_kwargs)
    
    if success:
        print(f"✓ 记录 {args.entry_id} 已更新")
        
        # 显示更新后的信息
        entry = store.get(args.entry_id)
        if args.hit:
            print(f"  当前命中次数: {entry['hit_count']}")
        if args.add_tags:
            print(f"  当前标签: {', '.join(entry['tags'])}")
    else:
        print(f"✗ 更新失败")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
