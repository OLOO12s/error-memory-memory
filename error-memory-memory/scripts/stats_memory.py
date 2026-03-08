#!/usr/bin/env python3
"""
错误记忆统计
用法: python stats_memory.py [--tags] [--top-errors]
"""

import argparse
import sys
from memory_store import get_store


def main():
    parser = argparse.ArgumentParser(
        description="错误记忆知识库统计",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stats_memory.py
  python stats_memory.py --tags
  python stats_memory.py --top-errors
        """
    )
    
    parser.add_argument("--tags", action="store_true",
                        help="显示标签分布")
    parser.add_argument("--top-errors", action="store_true",
                        help="显示最常遇到的问题")
    parser.add_argument("--limit", "-l", type=int, default=10,
                        help="显示数量限制")
    
    args = parser.parse_args()
    
    # 获取存储
    store = get_store()
    
    # 获取统计
    stats = store.get_stats()
    
    print("=" * 50)
    print("           错误记忆知识库统计")
    print("=" * 50)
    print()
    print(f"总记录数: {stats['total_entries']}")
    print(f"标签数量: {stats['total_tags']}")
    print(f"总命中次数: {stats['total_hits']}")
    print()
    
    # 标签分布
    if args.tags or (not args.top_errors):
        print("-" * 50)
        print("标签分布:")
        print("-" * 50)
        if stats['tag_distribution']:
            sorted_tags = sorted(
                stats['tag_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for tag, count in sorted_tags[:args.limit]:
                bar = "█" * (count * 2)
                print(f"  {tag:20s} {count:3d} {bar}")
        else:
            print("  暂无标签数据")
        print()
    
    # 最常遇到的问题
    if args.top_errors or (not args.tags):
        print("-" * 50)
        print("最常使用的问题解决:")
        print("-" * 50)
        entries = store.list_all(by_hits=True, recent=args.limit)
        if entries and entries[0].get('hit_count', 0) > 0:
            for i, entry in enumerate(entries, 1):
                if entry.get('hit_count', 0) == 0:
                    break
                print(f"  {i}. [{entry['id']}] 命中 {entry['hit_count']} 次")
                print(f"     {entry['error'][:50]}{'...' if len(entry['error']) > 50 else ''}")
        else:
            print("  暂无命中记录")
        print()
    
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
