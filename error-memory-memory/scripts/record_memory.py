#!/usr/bin/env python3
"""
记录新错误
用法: python record_memory.py --error "..." --solution "..." [--context "..."] [--tags "..."]
"""

import argparse
import sys
from memory_store import get_store


def main():
    parser = argparse.ArgumentParser(
        description="记录新的错误和解决方案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python record_memory.py \\
    --error "ModuleNotFoundError: No module named 'requests'" \\
    --solution "pip install requests" \\
    --tags "python,import"
  
  python record_memory.py \\
    --error "Blender渲染黑屏" \\
    --context "使用Cycles渲染器时" \\
    --solution "检查相机是否指向场景，或灯光强度是否足够" \\
    --cause "相机指向错误或灯光强度为0" \\
    --prevention "渲染前检查相机视角和灯光设置" \\
    --tags "blender,render,cycles"
        """
    )
    
    parser.add_argument("--error", "-e", required=True,
                        help="错误描述/症状（必填）")
    parser.add_argument("--solution", "-s", required=True,
                        help="解决方法（必填）")
    parser.add_argument("--context", "-c", default="",
                        help="发生场景/环境")
    parser.add_argument("--cause", default="",
                        help="根本原因分析")
    parser.add_argument("--prevention", "-p", default="",
                        help="预防措施")
    parser.add_argument("--tags", "-t", default="",
                        help="标签（逗号分隔）")
    parser.add_argument("--silent", action="store_true",
                        help="静默模式，只输出ID")
    
    args = parser.parse_args()
    
    # 获取存储
    store = get_store()
    
    # 添加记录
    entry_id = store.add(
        error=args.error,
        solution=args.solution,
        context=args.context,
        cause=args.cause,
        prevention=args.prevention,
        tags=args.tags
    )
    
    if args.silent:
        print(entry_id)
    else:
        print(f"[OK] 记录已保存: {entry_id}")
        print(f"  错误: {args.error[:60]}{'...' if len(args.error) > 60 else ''}")
        if args.tags:
            print(f"  标签: {args.tags}")
        print(f"\n下次遇到类似问题，使用以下命令查询:")
        print(f"  python scripts/query_memory.py \"{args.error[:30]}...\" --fuzzy")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
