#!/usr/bin/env python3
"""
查询错误记忆
用法: python query_memory.py "关键词" [--fuzzy] [--tag TAG] [--limit N]
"""

import argparse
import sys
from memory_store import get_store


def format_entry(entry: dict, detail: bool = False) -> str:
    """格式化输出单条记录"""
    lines = [
        "─" * 50,
        f"[{entry['id']}] {entry['error'][:60]}{'...' if len(entry['error']) > 60 else ''}",
    ]
    
    if detail:
        lines.extend([
            f"\n错误: {entry['error']}",
            f"场景: {entry.get('context', 'N/A')}",
            f"\n解决: {entry['solution']}",
        ])
        
        if entry.get('cause'):
            lines.append(f"\n原因: {entry['cause']}")
        if entry.get('prevention'):
            lines.append(f"\n预防: {entry['prevention']}")
    else:
        lines.append(f"解决: {entry['solution'][:80]}{'...' if len(entry['solution']) > 80 else ''}")
    
    if entry.get('tags'):
        lines.append(f"\n标签: {', '.join(entry['tags'])}")
    
    lines.append(f"命中: {entry.get('hit_count', 0)} 次 | 更新: {entry['updated_at'][:10]}")
    lines.append("─" * 50)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="查询错误记忆知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python query_memory.py "blender error"
  python query_memory.py "python" --fuzzy --limit 5
  python query_memory.py --tag "api"
        """
    )
    
    parser.add_argument("keyword", nargs="?", default="", 
                        help="查询关键词")
    parser.add_argument("--fuzzy", "-f", action="store_true",
                        help="启用模糊匹配")
    parser.add_argument("--tag", "-t", action="append", default=[],
                        help="按标签筛选（可多次使用）")
    parser.add_argument("--limit", "-l", type=int, default=10,
                        help="最多返回几条结果（默认10）")
    parser.add_argument("--detail", "-d", action="store_true",
                        help="显示详细信息")
    parser.add_argument("--format", choices=["text", "json", "context"], default="text",
                        help="输出格式")
    
    args = parser.parse_args()
    
    # 获取存储
    store = get_store()
    
    # 执行查询
    results = store.query(
        keyword=args.keyword,
        tags=args.tag if args.tag else None,
        fuzzy=args.fuzzy,
        limit=args.limit
    )
    
    # 输出结果
    if not results:
        print("未找到相关记录。")
        print(f"提示: 使用 --fuzzy 启用模糊匹配，或尝试其他关键词")
        return 1
    
    if args.format == "json":
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.format == "context":
        # 为AI助手提供上下文的格式
        print("## 相关知识库记录\n")
        for entry in results:
            print(f"### [{entry['id']}] {entry['error'][:50]}")
            print(f"**场景**: {entry.get('context', 'N/A')}")
            print(f"**解决**: {entry['solution']}")
            if entry.get('cause'):
                print(f"**原因**: {entry['cause']}")
            print()
    else:
        # 文本格式
        print(f"找到 {len(results)} 条相关记录:\n")
        for entry in results:
            print(format_entry(entry, detail=args.detail))
            print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
