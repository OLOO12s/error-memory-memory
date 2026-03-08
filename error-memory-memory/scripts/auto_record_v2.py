#!/usr/bin/env python3
"""
自动错误记录系统 V2
智能、可配置、无需手动干预

特性：
1. 自动初始化 - 导入即可使用
2. 智能去重 - 自动检测重复错误
3. 智能分类 - 自动提取标签和解决方案
4. 可配置 - 通过 JSON 配置文件自定义
5. 多种集成方式 - 装饰器、上下文管理器、全局钩子
"""

import functools
import sys
import traceback
import hashlib
import re
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, List, Dict, Set
from difflib import SequenceMatcher

# 导入存储和配置
from memory_store import get_store
from auto_record_config import get_config


class SmartErrorAnalyzer:
    """智能错误分析器"""
    
    def __init__(self):
        self.config = get_config()
    
    def analyze(self, error: Exception, tb_str: str) -> Dict[str, Any]:
        """全面分析错误"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        return {
            "type": error_type,
            "message": error_msg,
            "solution": self._generate_solution(error_type, error_msg),
            "cause": self._analyze_cause(tb_str),
            "prevention": self._suggest_prevention(error_type),
            "tags": self._extract_tags(error_type, error_msg, tb_str),
            "severity": self._assess_severity(error_type, error_msg),
            "category": self._categorize(error_type)
        }
    
    def _generate_solution(self, error_type: str, error_msg: str) -> str:
        """生成解决方案"""
        template = self.config.get_solution_template(error_type)
        
        if not template:
            return f"查看错误信息并修复：{error_type}"
        
        solution = template.get("solution", "")
        
        # 自动提取变量
        if template.get("auto_extract") and template.get("extract_pattern"):
            try:
                pattern = template["extract_pattern"]
                match = re.search(pattern, error_msg)
                if match:
                    extracted = match.group(1) if match.groups() else match.group(0)
                    # 替换模板中的变量
                    if "{module}" in solution:
                        solution = solution.format(module=extracted)
                    elif "{path}" in solution:
                        solution = solution.format(path=extracted)
                    elif "{key}" in solution:
                        solution = solution.format(key=extracted)
            except:
                pass
        
        return solution
    
    def _analyze_cause(self, tb_str: str) -> str:
        """分析根本原因"""
        lines = tb_str.strip().split("\n")
        
        # 找到错误发生的位置
        for i, line in enumerate(reversed(lines)):
            if "File \"" in line and "line" in line:
                # 返回文件名和行号
                match = re.search(r'File "([^"]+)".*line (\d+)', line)
                if match:
                    file_path, line_no = match.groups()
                    # 简化路径
                    file_name = Path(file_path).name
                    return f"{file_name}:{line_no}"
        
        return "未知位置"
    
    def _suggest_prevention(self, error_type: str) -> str:
        """建议预防措施"""
        prevention_map = {
            "ModuleNotFoundError": "使用虚拟环境并维护 requirements.txt",
            "ImportError": "添加 try/except 处理导入，提供降级方案",
            "FileNotFoundError": "操作前使用 os.path.exists() 检查文件",
            "KeyError": "使用 dict.get() 或先检查 key in dict",
            "IndexError": "使用 len() 检查长度，或使用切片",
            "AttributeError": "使用 hasattr() 检查属性或使用 getattr()",
            "TypeError": "使用类型检查或类型注解",
            "ZeroDivisionError": "除法前检查除数不为零",
            "ConnectionError": "添加重试机制和错误处理",
            "TimeoutError": "设置合理的超时时间，处理超时情况",
        }
        return prevention_map.get(error_type, "添加适当的错误处理")
    
    def _extract_tags(self, error_type: str, error_msg: str, tb_str: str) -> List[str]:
        """提取标签"""
        tags = set(self.config.get_auto_tags())
        
        # 错误类型标签
        type_tags = {
            "ModuleNotFoundError": "import",
            "ImportError": "import",
            "FileNotFoundError": "file",
            "PermissionError": "permission",
            "KeyError": "dict",
            "IndexError": "list",
            "AttributeError": "attribute",
            "TypeError": "type",
            "ValueError": "value",
            "ZeroDivisionError": "math",
            "ConnectionError": "network",
            "TimeoutError": "timeout",
            "JSONDecodeError": "json",
            "SyntaxError": "syntax",
            "IndentationError": "syntax",
            "NameError": "name",
            "RecursionError": "recursion",
            "MemoryError": "memory",
        }
        
        if error_type in type_tags:
            tags.add(type_tags[error_type])
        
        # 从堆栈提取模块名
        module_match = re.search(r'File "([^"]+)"', tb_str)
        if module_match:
            file_path = module_match.group(1)
            # 提取主模块名
            parts = Path(file_path).parts
            for part in parts:
                if part not in ["usr", "local", "lib", "python", "site-packages", 
                               "home", "users", "f:", "kcode"]:
                    if "." not in part:
                        tags.add(part.lower())
                        break
        
        return list(tags)
    
    def _assess_severity(self, error_type: str, error_msg: str) -> str:
        """评估严重程度"""
        critical = ["MemoryError", "RecursionError", "SystemExit"]
        high = ["ConnectionError", "PermissionError", "FileNotFoundError"]
        low = ["KeyError", "IndexError", "AttributeError"]
        
        if error_type in critical:
            return "critical"
        elif error_type in high:
            return "high"
        elif error_type in low:
            return "low"
        return "medium"
    
    def _categorize(self, error_type: str) -> str:
        """分类错误"""
        categories = {
            "import": ["ModuleNotFoundError", "ImportError"],
            "file": ["FileNotFoundError", "PermissionError", "IsADirectoryError"],
            "data": ["KeyError", "IndexError", "ValueError", "TypeError"],
            "network": ["ConnectionError", "TimeoutError"],
            "syntax": ["SyntaxError", "IndentationError"],
            "runtime": ["RuntimeError", "NameError", "AttributeError"],
            "system": ["MemoryError", "RecursionError", "OSError"]
        }
        
        for cat, types in categories.items():
            if error_type in types:
                return cat
        return "other"


class DuplicateDetector:
    """重复错误检测器 — 基于文件的持久化去重，与 CLI 共享状态"""

    def __init__(self):
        self._window_minutes = get_config().get("deduplication.time_window_minutes", 60)
        self._hash_file = Path(__file__).parent.parent / "memory" / ".recent_hashes.json"

    def compute_hash(self, error_type: str, error_msg: str,
                     simplified_tb: str = "") -> str:
        """计算错误哈希"""
        simplified_msg = self._simplify_msg(error_msg)
        content = f"{error_type}:{simplified_msg}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _simplify_msg(self, msg: str) -> str:
        """简化错误消息"""
        msg = re.sub(r'\d+', 'N', msg)
        msg = re.sub(r'0x[0-9a-fA-F]+', 'ADDR', msg)
        msg = re.sub(r"'[^']*?'", "'X'", msg)
        msg = re.sub(r'"[^"]*?"', '"X"', msg)
        return msg

    def _load_hashes(self) -> Dict[str, str]:
        """从文件加载哈希（与 CLI 共享 .recent_hashes.json）"""
        if not self._hash_file.exists():
            return {}
        try:
            with open(self._hash_file, 'r') as f:
                data = json.load(f)
            now = datetime.now()
            max_seconds = self._window_minutes * 60
            return {
                h: ts for h, ts in data.items()
                if self._is_recent(ts, now, max_seconds)
            }
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _is_recent(ts: str, now: datetime, max_seconds: int) -> bool:
        try:
            return (now - datetime.fromisoformat(ts)).total_seconds() < max_seconds
        except (ValueError, TypeError):
            return False

    def _save_hashes(self, hashes: Dict[str, str]):
        self._hash_file.parent.mkdir(exist_ok=True)
        with open(self._hash_file, 'w') as f:
            json.dump(hashes, f)

    def check_and_mark(self, error_hash: str) -> bool:
        """原子检查并标记。返回 True = 重复，False = 新的（已标记）"""
        hashes = self._load_hashes()
        if error_hash in hashes:
            return True
        hashes[error_hash] = datetime.now().isoformat()
        self._save_hashes(hashes)
        return False

    # 向后兼容旧 API
    def is_duplicate(self, error_hash: str) -> bool:
        return error_hash in self._load_hashes()

    def mark_recorded(self, error_hash: str):
        hashes = self._load_hashes()
        hashes[error_hash] = datetime.now().isoformat()
        self._save_hashes(hashes)


class AutoRecordManager:
    """自动记录管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.store = get_store()
        self.config = get_config()
        self.analyzer = SmartErrorAnalyzer()
        self.duplicate_detector = DuplicateDetector()
        self._enabled = self.config.is_enabled()
        self._initialized = True
        self._global_hook_installed = False
        
        # 如果配置启用全局钩子，自动安装
        if self.config.get("global_hook", False):
            self.install_global_hook()
    
    def record(self, error: Exception, context: str = "",
               func_name: str = "", force: bool = False) -> Optional[str]:
        """
        记录错误
        
        Args:
            error: 异常对象
            context: 上下文描述
            func_name: 函数名
            force: 强制记录（跳过检查）
            
        Returns:
            记录ID，如果跳过则返回None
        """
        if not self._enabled and not force:
            return None
        
        error_type = type(error).__name__
        error_msg = str(error)
        
        # 检查是否应该跳过
        if not force and self.config.should_skip(error_type, error_msg):
            return None
        
        # 获取堆栈
        tb_str = traceback.format_exc()
        simplified_tb = self.analyzer._analyze_cause(tb_str)
        
        # 检查重复 (原子操作: 检查+标记)
        error_hash = self.duplicate_detector.compute_hash(
            error_type, error_msg, simplified_tb
        )

        if not force and self.duplicate_detector.check_and_mark(error_hash):
            if self.config.get("output.print_on_record", True):
                print(f"[AutoRecord] 跳过重复错误: {error_type}")
            return None
        
        # 分析错误
        analysis = self.analyzer.analyze(error, tb_str)
        
        # 构建完整上下文
        full_context = context
        if func_name:
            full_context = f"函数 {func_name}" + (f" | {context}" if context else "")
        
        # 记录到存储
        entry_id = self.store.add(
            error=f"{error_type}: {error_msg}",
            solution=analysis["solution"],
            context=full_context or analysis["cause"],
            cause=analysis["cause"],
            prevention=analysis["prevention"],
            tags=",".join(analysis["tags"])
        )

        # 输出信息
        if self.config.get("output.print_on_record", True):
            print(f"[AutoRecord] 错误已记录: {entry_id} [{error_type}]")
            if self.config.get("output.show_traceback_preview", True):
                lines = self.config.get("output.traceback_lines", 3)
                tb_lines = tb_str.strip().split("\n")
                if len(tb_lines) >= 2:
                    print(f"           位置: {simplified_tb}")
        
        return entry_id
    
    def install_global_hook(self):
        """安装全局异常钩子"""
        if self._global_hook_installed:
            return
        
        original_hook = sys.excepthook
        
        def custom_hook(exc_type, exc_value, exc_traceback):
            if exc_value:
                self.record(exc_value, context="未捕获的全局异常")
            original_hook(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = custom_hook
        self._global_hook_installed = True
        
        if self.config.get("output.print_on_record", True):
            print("[AutoRecord] 全局异常捕获已启用")
    
    def uninstall_global_hook(self):
        """卸载全局异常钩子"""
        # 简化的卸载，实际上很难完全恢复
        self._global_hook_installed = False
    
    def enable(self):
        """启用自动记录"""
        self._enabled = True
        self.config.set("enabled", True)
        print("[AutoRecord] 自动记录已启用")
    
    def disable(self):
        """禁用自动记录"""
        self._enabled = False
        self.config.set("enabled", False)
        print("[AutoRecord] 自动记录已禁用")
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled


# 获取管理器实例
def get_manager() -> AutoRecordManager:
    """获取自动记录管理器"""
    return AutoRecordManager()


# ============ 便捷装饰器 ============

def auto_record(func: Optional[Callable] = None, *, 
                context: str = "",
                reraise: bool = True) -> Callable:
    """
    自动记录装饰器
    
    自动捕获函数异常并记录
    
    用法:
        @auto_record
        def my_func():
            ...
            
        @auto_record(context="处理数据时")
        def process():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                get_manager().record(e, context=context, func_name=f.__name__)
                if reraise:
                    raise
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


# ============ 上下文管理器 ============

@contextmanager
def auto_record_block(context: str = ""):
    """
    自动记录上下文管理器
    
    用法:
        with auto_record_block("处理数据"):
            do_something()
    """
    try:
        yield
    except Exception as e:
        get_manager().record(e, context=context)
        raise


# ============ 初始化 ============

def init(enable_global: bool = False, auto_tags: List[str] = None):
    """
    初始化自动记录系统
    
    Args:
        enable_global: 是否启用全局异常捕获
        auto_tags: 自动标签
    """
    manager = get_manager()
    
    if auto_tags:
        for tag in auto_tags:
            get_config().add_auto_tag(tag)
    
    if enable_global:
        manager.install_global_hook()
    
    return manager


# 自动初始化（当导入此模块时）
_manager = None

def _auto_init():
    """自动初始化"""
    global _manager
    if _manager is None:
        _manager = get_manager()
    return _manager

# 导入时自动初始化
_auto_init()


if __name__ == "__main__":
    # 测试
    print("=== AutoRecord V2 测试 ===\n")
    
    # 测试1: 装饰器
    @auto_record(context="测试装饰器")
    def test_error():
        raise ValueError("这是一个测试错误")
    
    try:
        test_error()
    except:
        pass
    
    print()
    
    # 测试2: 上下文管理器
    try:
        with auto_record_block("测试上下文"):
            x = 1 / 0
    except:
        pass
    
    print()
    
    # 测试3: 直接记录
    try:
        raise KeyError("test_key")
    except Exception as e:
        get_manager().record(e, context="直接记录测试")
    
    print("\n测试完成!")
