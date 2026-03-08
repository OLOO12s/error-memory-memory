#!/usr/bin/env python3
"""
导出错误记忆
用法: python export_memory.py --format [json|markdown] --output file
"""

import argparse
import json
import sys
from memory_store import get_store


def export_json(entries: list, output_file: str):
    """导出为JSON格式"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def export_markdown(entries: list, output_file: str):
    """导出为Markdown格式"""
    lines = [
        "# 错误记忆知识库",
        "",
        f"> 共 {len(entries)} 条记录",
        f"> 导出时间: {__import__('datetime').datetime.now().isoformat()}",
        "",
        "---",
        "",
    ]
    
    for entry in entries:
        lines.extend([
            f"## [{entry['id']}] {entry['error']}",
            "",
            f"**场景**: {entry.get('context', 'N/A')}",
            "",
            f"**解决方法**:",
            f"```",
            f"{entry['solution']}",
            f"```",
            "",
        ])
        
        if entry.get('cause'):
            lines.extend([
                f"**根本原因**: {entry['cause']}",
                "",
            ])
        
        if entry.get('prevention'):
            lines.extend([
                f"**预防措施**: {entry['prevention']}",
                "",
            ])
        
        if entry.get('tags'):
            lines.extend([
                f"**标签**: {', '.join(entry['tags'])}",
                "",
            ])
        
        lines.extend([
            f"*创建时间: {entry['created_at'][:10]} | 命中次数: {entry.get('hit_count', 0)}*",
            "",
            "---",
            "",
        ])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="导出错误记忆知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python export_memory.py --format json --output backup.json
  python export_memory.py --format markdown --output notes.md
        """
    )
    
    parser.add_argument("--format", "-f", choices=["json", "markdown"], required=True,
                        help="导出格式")
    parser.add_argument("--output", "-o", required=True,
                        help="输出文件路径")
    parser.add_argument("--tag", "-t", default="",
                        help="只导出特定标签的记录")
    
    args = parser.parse_args()
    
    # 获取存储
    store = get_store()
    
    # 获取记录
    entries = store.list_all(tag=args.tag)
    
    if not entries:
        print("没有记录可导出")
        return 1
    
    # 导出
    try:
        if args.format == "json":
            export_json(entries, args.output)
        else:
            export_markdown(entries, args.output)
        
        print(f"✓ 已导出 {len(entries)} 条记录到: {args.output}")
        return 0
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
