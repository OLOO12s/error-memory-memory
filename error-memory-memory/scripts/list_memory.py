#!/usr/bin/env python3
"""
列出所有错误记录
用法: python list_memory.py [--tag TAG] [--recent N] [--by-hits]
"""

import argparse
import sys
from memory_store import get_store


def format_entry(entry: dict) -> str:
    """格式化输出单条记录"""
    tags_str = f" [{', '.join(entry['tags'])}]" if entry.get('tags') else ""
    return (
        f"[{entry['id']}] {entry['error'][:50]}{'...' if len(entry['error']) > 50 else ''}{tags_str}\n"
        f"    解决: {entry['solution'][:60]}{'...' if len(entry['solution']) > 60 else ''}\n"
        f"    命中: {entry.get('hit_count', 0)} 次 | {entry['updated_at'][:10]}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="列出所有错误记录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python list_memory.py
  python list_memory.py --tag "blender"
  python list_memory.py --recent 10
  python list_memory.py --by-hits
        """
    )
    
    parser.add_argument("--tag", "-t", default="",
                        help="按标签筛选")
    parser.add_argument("--recent", "-r", type=int, default=0,
                        help="只显示最近N条")
    parser.add_argument("--by-hits", action="store_true",
                        help="按使用频率排序")
    
    args = parser.parse_args()
    
    # 获取存储
    store = get_store()
    
    # 获取记录
    results = store.list_all(
        tag=args.tag,
        by_hits=args.by_hits,
        recent=args.recent
    )
    
    if not results:
        filter_desc = f"标签 '{args.tag}' 的" if args.tag else ""
        print(f"暂无{filter_desc}记录。")
        return 1
    
    # 显示统计
    stats = store.get_stats()
    print(f"共 {stats['total_entries']} 条记录")
    if args.tag:
        print(f"标签 '{args.tag}' 有 {len(results)} 条\n")
    else:
        print(f"共 {stats['total_tags']} 个标签\n")
    
    # 输出结果
    for i, entry in enumerate(results, 1):
        print(format_entry(entry))
        if i < len(results):
            print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
