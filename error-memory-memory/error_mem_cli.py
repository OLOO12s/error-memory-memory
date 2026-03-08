#!/usr/bin/env python3
"""
Error Memory CLI - 通用错误记忆系统入口
可从任何位置、任何 AI 工具、任何终端调用

用法:
    python error_mem_cli.py record -e "错误描述" -s "解决方法" [-t "标签"]
    python error_mem_cli.py query "关键词"
    python error_mem_cli.py list [--recent N] [--tag TAG]
    python error_mem_cli.py stats
    python error_mem_cli.py hook-stdin          # 读取 stdin JSON (AI hook 通用接口)
    python error_mem_cli.py exec -- cmd args    # 包装命令执行，自动捕获错误
"""

import sys
import os
import io
import json
import argparse
import subprocess
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# Windows 编码兼容: 强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# === 路径设置 ===
SKILL_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"
MEMORY_DIR = SKILL_DIR / "memory"
CONFIG_FILE = SKILL_DIR / "config" / "auto_record.json"

# 添加 scripts 到 sys.path 以复用已有模块
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from memory_store import get_store
    from auto_record_config import get_config
except ImportError:
    # 回退: 如果导入失败，使用内置简化版
    _store = None
    _config = None

    def get_store():
        global _store
        if _store is None:
            sys.path.insert(0, str(SCRIPTS_DIR))
            from memory_store import get_store as gs
            _store = gs()
        return _store

    def get_config():
        global _config
        if _config is None:
            sys.path.insert(0, str(SCRIPTS_DIR))
            from auto_record_config import get_config as gc
            _config = gc()
        return _config


# === 错误分析工具 ===

# 常见命令失败但不是真正错误的模式
NOISE_PATTERNS = [
    r"^grep .* returned exit code 1$",  # grep 没匹配
    r"^test .* returned",               # test 条件不满足
    r"^\[.* returned",                  # [ ] 条件测试
    r"^diff .* returned",              # diff 有差异
    r"^which .* returned",             # which 没找到
    r"^command .* not found",          # 不关键的命令
    r"^false$",                        # 意图性的 false
]

# 错误严重程度关键词
ERROR_KEYWORDS = [
    "error", "Error", "ERROR",
    "exception", "Exception", "EXCEPTION",
    "traceback", "Traceback",
    "failed", "Failed", "FAILED",
    "fatal", "Fatal", "FATAL",
    "segfault", "Segmentation fault",
    "panic", "PANIC",
    "denied", "Permission denied",
    "not found", "No such file",
    "ModuleNotFoundError", "ImportError",
    "SyntaxError", "IndentationError",
    "TypeError", "ValueError", "KeyError",
    "AttributeError", "NameError",
    "RuntimeError", "OSError", "IOError",
    "ConnectionError", "TimeoutError",
]


def is_noise(error_text: str) -> bool:
    """检查是否是噪音（非真正错误）"""
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, error_text, re.IGNORECASE):
            return True
    return False


def has_error_indicators(text: str) -> bool:
    """检查文本是否包含错误指标"""
    for keyword in ERROR_KEYWORDS:
        if keyword in text:
            return True
    return False


def extract_error_info(text: str) -> Dict[str, str]:
    """从文本中提取错误信息"""
    info = {"error": "", "error_type": "", "context": ""}

    # Python traceback
    tb_match = re.search(
        r'(Traceback \(most recent call last\):.*?)(?:\n\n|\Z)',
        text, re.DOTALL
    )
    if tb_match:
        tb_text = tb_match.group(1)
        # 提取最后一行错误
        lines = tb_text.strip().split("\n")
        if lines:
            info["error"] = lines[-1].strip()
            # 提取错误类型
            type_match = re.match(r'^(\w+Error|\w+Exception|\w+Warning)', info["error"])
            if type_match:
                info["error_type"] = type_match.group(1)
        # 提取文件位置作为上下文
        file_match = re.findall(r'File "([^"]+)", line (\d+)', tb_text)
        if file_match:
            last_file, last_line = file_match[-1]
            info["context"] = f"{Path(last_file).name}:{last_line}"
        return info

    # 通用错误行
    for keyword in ERROR_KEYWORDS:
        idx = text.find(keyword)
        if idx != -1:
            # 提取包含关键词的那一行
            start = text.rfind("\n", 0, idx) + 1
            end = text.find("\n", idx)
            if end == -1:
                end = len(text)
            error_line = text[start:end].strip()
            if error_line and len(error_line) < 500:
                info["error"] = error_line
                break

    if not info["error"] and text.strip():
        # 取最后几行作为错误信息
        lines = text.strip().split("\n")
        info["error"] = lines[-1][:200] if lines else text[:200]

    return info


def generate_solution(error_type: str, error_msg: str) -> str:
    """根据错误类型生成解决方案建议"""
    solutions = {
        "ModuleNotFoundError": "安装缺失模块",
        "ImportError": "检查模块安装和导入路径",
        "FileNotFoundError": "检查文件路径是否正确",
        "PermissionError": "检查文件/目录权限",
        "KeyError": "检查字典键是否存在，使用 .get() 方法",
        "IndexError": "检查列表/数组索引范围",
        "AttributeError": "检查对象类型和属性名",
        "TypeError": "检查参数类型是否匹配",
        "ValueError": "检查参数值是否在有效范围内",
        "ZeroDivisionError": "除法前检查除数不为零",
        "ConnectionError": "检查网络连接",
        "TimeoutError": "增加超时时间或检查服务状态",
        "SyntaxError": "检查语法，特别是括号和缩进",
        "NameError": "检查变量/函数名是否已定义",
        "RuntimeError": "查看详细错误信息",
    }

    # 精确匹配
    if error_type in solutions:
        base = solutions[error_type]
        # 尝试提取更多细节
        if error_type == "ModuleNotFoundError":
            match = re.search(r"'([^']+)'", error_msg)
            if match:
                return f"{base}: pip install {match.group(1)}"
        return base

    return "待分析 - 需要手动填写解决方案"


def compute_error_hash(error_type: str, error_msg: str) -> str:
    """计算错误哈希用于去重"""
    # 简化错误消息（去掉变化部分）
    simplified = re.sub(r'\d+', 'N', error_msg)
    simplified = re.sub(r'0x[0-9a-fA-F]+', 'ADDR', simplified)
    simplified = re.sub(r"'[^']*?'", "'X'", simplified)
    content = f"{error_type}:{simplified}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


# === 去重检查 ===

DEDUP_FILE = MEMORY_DIR / ".recent_hashes.json"


def load_recent_hashes() -> Dict[str, str]:
    """加载最近的错误哈希"""
    if DEDUP_FILE.exists():
        try:
            with open(DEDUP_FILE, 'r') as f:
                data = json.load(f)
            # 清理过期记录（1小时内）
            now = datetime.now()
            cleaned = {}
            for h, ts in data.items():
                try:
                    t = datetime.fromisoformat(ts)
                    if (now - t).total_seconds() < 3600:
                        cleaned[h] = ts
                except:
                    pass
            return cleaned
        except:
            return {}
    return {}


def save_recent_hashes(hashes: Dict[str, str]):
    """保存最近的错误哈希"""
    MEMORY_DIR.mkdir(exist_ok=True)
    with open(DEDUP_FILE, 'w') as f:
        json.dump(hashes, f)


def is_duplicate(error_hash: str) -> bool:
    """检查是否是重复错误"""
    hashes = load_recent_hashes()
    return error_hash in hashes


def mark_recorded(error_hash: str):
    """标记为已记录"""
    hashes = load_recent_hashes()
    hashes[error_hash] = datetime.now().isoformat()
    save_recent_hashes(hashes)


# === 命令实现 ===

def cmd_record(args):
    """记录错误"""
    store = get_store()

    error_text = args.error
    solution = args.solution or generate_solution(
        args.error_type or "", error_text
    )
    context = args.context or ""
    tags = args.tags or "auto-captured"

    # 去重检查
    if not args.force:
        eh = compute_error_hash(args.error_type or "", error_text)
        if is_duplicate(eh):
            if not args.silent:
                print(f"[ErrorMem] 跳过重复错误")
            return None
        mark_recorded(eh)

    entry_id = store.add(
        error=error_text,
        solution=solution,
        context=context,
        cause=args.cause or "",
        prevention=args.prevention or "",
        tags=tags
    )

    if not args.silent:
        print(f"[ErrorMem] ✓ 已记录: {entry_id}")
        print(f"  错误: {error_text[:80]}{'...' if len(error_text) > 80 else ''}")
        if tags:
            print(f"  标签: {tags}")

    return entry_id


def cmd_query(args):
    """查询错误"""
    store = get_store()
    keyword = args.keyword
    results = store.query(keyword=keyword, fuzzy=True, limit=args.limit or 5)

    if not results:
        print(f"[ErrorMem] 未找到与 '{keyword}' 相关的记录")
        return []

    print(f"[ErrorMem] 找到 {len(results)} 条相关记录:\n")
    for r in results:
        print(f"  [{r['id']}] {r.get('error', '')[:80]}")
        if r.get('solution'):
            print(f"    解决: {r['solution'][:80]}")
        if r.get('tags'):
            print(f"    标签: {', '.join(r['tags'])}")
        print()

    return results


def cmd_list(args):
    """列出记录"""
    store = get_store()
    results = store.list_all(
        tag=args.tag or "",
        by_hits=args.by_hits,
        recent=args.recent or 0
    )

    if not results:
        print("[ErrorMem] 知识库为空")
        return

    print(f"[ErrorMem] 共 {len(results)} 条记录:\n")
    for r in results:
        print(f"  [{r['id']}] {r.get('error', '')[:80]}")
        if r.get('solution') and r['solution'] != '待分析 - 需要手动填写解决方案':
            print(f"    → {r['solution'][:80]}")
        hits = r.get('hit_count', 0)
        if hits:
            print(f"    命中: {hits}次")
        print()


def cmd_stats(args):
    """统计信息"""
    store = get_store()
    stats = store.get_stats()

    print(f"[ErrorMem] 统计信息:")
    print(f"  总记录数: {stats['total_entries']}")
    print(f"  总标签数: {stats['total_tags']}")
    print(f"  总命中次数: {stats['total_hits']}")

    if stats.get('tag_distribution'):
        print(f"\n  标签分布:")
        sorted_tags = sorted(
            stats['tag_distribution'].items(),
            key=lambda x: x[1], reverse=True
        )
        for tag, count in sorted_tags[:15]:
            print(f"    {tag}: {count}")


def cmd_update(args):
    """更新记录"""
    store = get_store()
    kwargs = {}
    if args.solution:
        kwargs['solution'] = args.solution
    if args.context:
        kwargs['context'] = args.context
    if args.add_tags:
        kwargs['add_tags'] = args.add_tags
    if args.hit:
        kwargs['hit'] = True

    success = store.update(args.entry_id, **kwargs)
    if success:
        print(f"[ErrorMem] ✓ 已更新: {args.entry_id}")
    else:
        print(f"[ErrorMem] ✗ 未找到: {args.entry_id}")


def cmd_exec(args):
    """包装命令执行，自动捕获错误"""
    cmd = args.command
    if not cmd:
        print("[ErrorMem] 用法: error_mem_cli.py exec -- command args")
        sys.exit(1)

    # 执行命令
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            timeout=args.timeout or 300
        )

        # 输出原始结果
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr)

        # 检查是否有错误
        if result.returncode != 0:
            combined = (result.stderr or '') + (result.stdout or '')
            if not is_noise(combined):
                error_info = extract_error_info(combined)
                error_text = error_info["error"] or f"Command failed (exit {result.returncode})"

                # 记录错误
                store = get_store()
                cmd_str = cmd if isinstance(cmd, str) else ' '.join(cmd)
                entry_id = store.add(
                    error=error_text,
                    solution=generate_solution(
                        error_info.get("error_type", ""),
                        error_text
                    ),
                    context=f"命令: {cmd_str[:200]}",
                    tags="shell,auto-captured"
                )
                print(f"\n[ErrorMem] ✓ 错误已自动记录: {entry_id}",
                      file=sys.stderr)

                # 查询相似错误
                results = store.query(keyword=error_text[:50], fuzzy=True, limit=3)
                if len(results) > 1:  # 排除刚刚记录的
                    print(f"[ErrorMem] 💡 发现 {len(results)-1} 条类似历史记录:",
                          file=sys.stderr)
                    for r in results:
                        if r['id'] != entry_id:
                            print(f"  [{r['id']}] {r.get('solution', '')[:60]}",
                                  file=sys.stderr)

        sys.exit(result.returncode)

    except subprocess.TimeoutExpired:
        print(f"[ErrorMem] 命令超时", file=sys.stderr)
        sys.exit(124)
    except Exception as e:
        print(f"[ErrorMem] 执行失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_hook_stdin(args):
    """
    通用 AI Hook 处理器
    从 stdin 读取 JSON，检测并记录错误
    支持 Claude Code PostToolUse、以及任何发送 JSON 的 AI 工具

    输入格式 (兼容多种AI工具):
    {
        "tool_name": "Bash",
        "tool_input": {"command": "..."},
        "tool_response": "..." 或 {"stdout": "...", "stderr": "...", "exitCode": N}
    }
    """
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # 无效输入，静默退出

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_response = data.get("tool_response", data.get("tool_output", ""))

    # 提取响应文本
    if isinstance(tool_response, dict):
        response_text = json.dumps(tool_response, ensure_ascii=False)
        exit_code = tool_response.get("exitCode",
                     tool_response.get("exit_code",
                      tool_response.get("returncode", 0)))
    elif isinstance(tool_response, str):
        response_text = tool_response
        # 尝试从文本中提取 exit code
        exit_match = re.search(r'exit (?:code|status)[:\s]*(\d+)', response_text, re.I)
        exit_code = int(exit_match.group(1)) if exit_match else 0
    else:
        sys.exit(0)

    # 判断是否有错误
    is_bash = tool_name == "Bash" or "bash" in tool_name.lower()
    is_mcp = "mcp__" in tool_name
    has_error = False

    if is_bash:
        if exit_code != 0:
            has_error = True
        elif has_error_indicators(response_text):
            has_error = True
    elif is_mcp:
        if has_error_indicators(response_text):
            has_error = True
    else:
        if has_error_indicators(response_text):
            has_error = True

    if not has_error:
        sys.exit(0)

    # 过滤噪音
    if is_noise(response_text):
        sys.exit(0)

    # 提取错误信息
    error_info = extract_error_info(response_text)
    error_text = error_info["error"] or f"Tool error: {tool_name}"

    # 去重检查
    eh = compute_error_hash(error_info.get("error_type", ""), error_text)
    if is_duplicate(eh):
        sys.exit(0)

    # 记录错误
    store = get_store()

    # 构建上下文
    if is_bash:
        cmd = tool_input.get("command", "")
        context = f"命令: {cmd[:300]}"
    elif is_mcp:
        context = f"工具: {tool_name}"
    else:
        context = f"工具: {tool_name}"

    tags_list = ["auto-captured"]
    if is_bash:
        tags_list.append("shell")
    if is_mcp:
        tags_list.append("mcp")
        # 提取 MCP 服务名
        parts = tool_name.split("__")
        if len(parts) >= 2:
            tags_list.append(parts[1])
    if error_info.get("error_type"):
        tags_list.append(error_info["error_type"].lower())

    entry_id = store.add(
        error=error_text[:500],
        solution=generate_solution(
            error_info.get("error_type", ""),
            error_text
        ),
        context=context,
        tags=",".join(tags_list)
    )
    mark_recorded(eh)

    # 查询相似历史错误
    similar = store.query(keyword=error_text[:50], fuzzy=True, limit=3)
    past_solutions = [
        r for r in similar
        if r['id'] != entry_id
        and r.get('solution')
        and r['solution'] != '待分析 - 需要手动填写解决方案'
    ]

    # 输出结果 (JSON格式，AI工具可解析)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": ""
        }
    }

    context_parts = [f"[ErrorMem] 错误已自动记录: {entry_id}"]
    if past_solutions:
        context_parts.append(f"发现 {len(past_solutions)} 条类似历史记录:")
        for r in past_solutions[:3]:
            context_parts.append(
                f"  [{r['id']}] {r.get('error', '')[:60]}"
                f"\n    解决方案: {r.get('solution', '')[:100]}"
            )
        context_parts.append(
            "建议先查看历史解决方案再尝试修复。"
        )

    output["hookSpecificOutput"]["additionalContext"] = "\n".join(context_parts)

    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)


# === 主入口 ===

def main():
    parser = argparse.ArgumentParser(
        prog="error-mem",
        description="通用错误记忆系统 - 记录、查询、复用问题解决经验",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s record -e "ImportError: No module named 'xxx'" -s "pip install xxx"
  %(prog)s query "ImportError"
  %(prog)s list --recent 10
  %(prog)s stats
  %(prog)s exec -- python script.py
  echo '{"tool_name":"Bash",...}' | %(prog)s hook-stdin
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # record
    p_record = subparsers.add_parser("record", aliases=["r"],
                                      help="记录新错误")
    p_record.add_argument("-e", "--error", required=True, help="错误描述")
    p_record.add_argument("-s", "--solution", help="解决方法")
    p_record.add_argument("-c", "--context", help="发生场景")
    p_record.add_argument("-t", "--tags", help="标签（逗号分隔）")
    p_record.add_argument("--cause", help="根本原因")
    p_record.add_argument("--prevention", help="预防措施")
    p_record.add_argument("--error-type", help="错误类型")
    p_record.add_argument("--force", action="store_true", help="强制记录（跳过去重）")
    p_record.add_argument("--silent", action="store_true", help="静默模式")

    # query
    p_query = subparsers.add_parser("query", aliases=["q"],
                                     help="查询历史记录")
    p_query.add_argument("keyword", help="搜索关键词")
    p_query.add_argument("-l", "--limit", type=int, default=5, help="结果数量")

    # list
    p_list = subparsers.add_parser("list", aliases=["ls"],
                                    help="列出所有记录")
    p_list.add_argument("--tag", help="按标签筛选")
    p_list.add_argument("--recent", type=int, help="最近N条")
    p_list.add_argument("--by-hits", action="store_true", help="按命中排序")

    # stats
    subparsers.add_parser("stats", help="统计信息")

    # update
    p_update = subparsers.add_parser("update", aliases=["u"],
                                      help="更新记录")
    p_update.add_argument("entry_id", help="记录ID (如 ERR-001)")
    p_update.add_argument("-s", "--solution", help="新的解决方案")
    p_update.add_argument("-c", "--context", help="新的上下文")
    p_update.add_argument("--add-tags", help="追加标签")
    p_update.add_argument("--hit", action="store_true", help="增加命中计数")

    # exec
    p_exec = subparsers.add_parser("exec", help="包装命令，自动捕获错误")
    p_exec.add_argument("exec_cmd", nargs=argparse.REMAINDER, help="要执行的命令")
    p_exec.add_argument("--timeout", type=int, default=300, help="超时秒数")

    # hook-stdin
    subparsers.add_parser("hook-stdin", help="AI Hook 处理器（从 stdin 读取 JSON）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 分发命令
    cmd = args.command
    if cmd in ("record", "r"):
        cmd_record(args)
    elif cmd in ("query", "q"):
        cmd_query(args)
    elif cmd in ("list", "ls"):
        cmd_list(args)
    elif cmd == "stats":
        cmd_stats(args)
    elif cmd in ("update", "u"):
        cmd_update(args)
    elif cmd == "exec":
        # 处理 -- 分隔符
        if hasattr(args, 'exec_cmd'):
            args.command = args.exec_cmd
        if args.command and args.command[0] == '--':
            args.command = args.command[1:]
        cmd_exec(args)
    elif cmd == "hook-stdin":
        cmd_hook_stdin(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
