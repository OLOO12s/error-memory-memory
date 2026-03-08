#!/bin/bash
# ============================================================
# Error Memory - Shell 自动错误捕获
# ============================================================
#
# 使用方法 (添加到 ~/.bashrc 或在终端中运行):
#
#   source /f/KCODE/.agents/skills/error-memory-memory/shell_integration.sh
#
# 功能:
#   1. 自动捕获失败的命令并记录到错误知识库
#   2. 提供便捷命令: em-record, em-query, em-list
#   3. 使用 errmem 包装命令执行以获得更详细的错误捕获
#
# 兼容: Git Bash (Windows), Bash (Linux/Mac), Zsh
# ============================================================

# 获取脚本所在目录
if [[ -n "${BASH_SOURCE[0]}" ]]; then
    _ERRMEM_SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [[ -n "${(%):-%x}" ]]; then
    # Zsh 兼容
    _ERRMEM_SKILL_DIR="$(cd "$(dirname "${(%):-%x}")" && pwd)"
else
    _ERRMEM_SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

_ERRMEM_CLI="$_ERRMEM_SKILL_DIR/error_mem_cli.py"

# 检查 Python 是否可用
if command -v python3 &>/dev/null; then
    _ERRMEM_PYTHON="python3"
elif command -v python &>/dev/null; then
    _ERRMEM_PYTHON="python"
else
    echo "[ErrorMem] ⚠ Python 未找到，Shell 集成已禁用"
    return 1 2>/dev/null || exit 1
fi

# ============================================================
# 方式 1: trap ERR 自动捕获 (轻量级)
# ============================================================
# 捕获失败的命令名和退出码，但不包含 stderr 内容
# 适合自动后台运行

# 需要跳过的命令模式 (这些命令返回非零不算错误)
_ERRMEM_SKIP_CMDS="grep|test|\\[|diff|which|command|true|false|:|exit"

_errmem_trap_handler() {
    local exit_code=$?
    local last_cmd="$BASH_COMMAND"

    # 跳过非错误的命令
    if [[ "$last_cmd" =~ ^($_ERRMEM_SKIP_CMDS) ]]; then
        return
    fi

    # 跳过 Ctrl+C (exit 130)
    if [[ $exit_code -eq 130 ]]; then
        return
    fi

    # 后台异步记录，不阻塞终端
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" record \
        -e "Shell: $last_cmd (exit $exit_code)" \
        -c "终端自动捕获" \
        -t "shell,auto-captured" \
        --silent 2>/dev/null &
}

# 安装 trap (仅在交互式 shell 中)
if [[ $- == *i* ]]; then
    trap _errmem_trap_handler ERR
fi

# ============================================================
# 方式 2: errmem 命令包装器 (详细捕获)
# ============================================================
# 包装命令执行，捕获完整的 stdout/stderr
# 用法: errmem python script.py

errmem() {
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" exec -- "$@"
}

# ============================================================
# 便捷命令
# ============================================================

# 记录错误
em-record() {
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" record "$@"
}

# 查询历史
em-query() {
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" query "$@"
}

# 列出记录
em-list() {
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" list "$@"
}

# 统计
em-stats() {
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" stats
}

# 更新记录
em-update() {
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" update "$@"
}

# 完整 CLI
error-mem() {
    $_ERRMEM_PYTHON "$_ERRMEM_CLI" "$@"
}

# ============================================================
# 启动提示
# ============================================================

if [[ $- == *i* ]]; then
    echo "[ErrorMem] ✓ Shell 错误自动捕获已启用"
    echo "  命令: em-query <关键词> | em-list | em-record | em-stats"
    echo "  包装: errmem <命令>   (捕获完整错误输出)"
fi
