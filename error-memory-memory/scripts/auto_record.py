#!/usr/bin/env python3
"""
自动错误记录系统
提供装饰器、上下文管理器等方式自动捕获和记录错误
无需手动运行 record_memory.py

核心功能：
1. @auto_record 装饰器 - 自动记录函数异常
2. AutoRecordContext 上下文管理器 - 自动记录代码块异常
3. 重复错误检测 - 避免重复记录相同错误
4. 智能分类 - 自动提取标签和上下文
"""

import functools
import sys
import traceback
import hashlib
import re
from contextlib import contextmanager
from typing import Optional, Callable, Any, List, Dict
from memory_store import get_store


class AutoRecorder:
    """自动记录器核心类"""
    
    def __init__(self):
        self.store = get_store()
        self._recorded_hashes = set()  # 已记录的错误哈希，用于去重
        self._enabled = True
        self._auto_tags = []  # 自动添加的标签
        self._context_provider = None  # 上下文提供函数
        self._skip_patterns = []  # 跳过的错误模式
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 默认配置
        self._skip_patterns = [
            r"KeyboardInterrupt",
            r"SystemExit",
            r"pytest_",
            r"unittest\.",
        ]
    
    def _compute_error_hash(self, error_type: str, error_msg: str, 
                           traceback_str: str) -> str:
        """计算错误的唯一哈希，用于去重"""
        # 简化错误信息，去除行号等变化部分
        simplified = f"{error_type}:{self._simplify_error_msg(error_msg)}"
        return hashlib.md5(simplified.encode()).hexdigest()[:12]
    
    def _simplify_error_msg(self, msg: str) -> str:
        """简化错误信息，去除变化部分"""
        # 去除文件路径、行号、内存地址等
        msg = re.sub(r'File "[^"]+"', 'File "..."', msg)
        msg = re.sub(r'line \d+', 'line X', msg)
        msg = re.sub(r'0x[0-9a-fA-F]+', '0x...', msg)
        msg = re.sub(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', 'DATE', msg)
        return msg
    
    def _should_skip(self, error: Exception) -> bool:
        """判断是否应该跳过此错误"""
        error_str = f"{type(error).__name__}: {str(error)}"
        
        for pattern in self._skip_patterns:
            if re.search(pattern, error_str):
                return True
        
        return False
    
    def _extract_auto_tags(self, error: Exception, func_name: str = "") -> List[str]:
        """自动提取标签"""
        tags = set(self._auto_tags)
        
        # 根据错误类型添加标签
        error_type = type(error).__name__
        error_module = type(error).__module__
        
        if error_module.startswith("builtins"):
            tags.add("python")
        else:
            tags.add(error_module.split(".")[0])
        
        # 常见错误类型映射
        type_tags = {
            "ModuleNotFoundError": "import",
            "ImportError": "import",
            "FileNotFoundError": "file",
            "PermissionError": "permission",
            "ConnectionError": "network",
            "TimeoutError": "timeout",
            "KeyError": "dict",
            "IndexError": "list",
            "AttributeError": "attribute",
            "TypeError": "type",
            "ValueError": "value",
            "ZeroDivisionError": "math",
        }
        
        if error_type in type_tags:
            tags.add(type_tags[error_type])
        
        # 根据函数名添加标签
        if func_name:
            tags.add(func_name.split("_")[0])
        
        return list(tags)
    
    def _extract_context(self, error: Exception, func_name: str = "",
                        extra_context: str = "") -> str:
        """提取发生场景"""
        contexts = []
        
        if func_name:
            contexts.append(f"函数: {func_name}")
        
        if extra_context:
            contexts.append(extra_context)
        
        # 尝试从异常中提取有用信息
        error_str = str(error)
        if "'" in error_str and ("not found" in error_str or "No module" in error_str):
            contexts.append("模块/依赖缺失")
        
        return " | ".join(contexts) if contexts else "自动捕获"
    
    def record(self, error: Exception, func_name: str = "", 
               extra_context: str = "", force: bool = False) -> Optional[str]:
        """
        记录错误
        
        Args:
            error: 异常对象
            func_name: 函数名（可选）
            extra_context: 额外上下文（可选）
            force: 强制记录，即使重复
            
        Returns:
            记录ID，如果跳过则返回None
        """
        if not self._enabled and not force:
            return None
        
        if not force and self._should_skip(error):
            return None
        
        error_type = type(error).__name__
        error_msg = str(error)
        tb_str = traceback.format_exc()
        
        # 计算哈希检查是否重复
        error_hash = self._compute_error_hash(error_type, error_msg, tb_str)
        
        if not force and error_hash in self._recorded_hashes:
            return None  # 已记录过
        
        self._recorded_hashes.add(error_hash)
        
        # 构建解决方案建议
        solution = self._suggest_solution(error, tb_str)
        
        # 提取标签和上下文
        tags = self._extract_auto_tags(error, func_name)
        context = self._extract_context(error, func_name, extra_context)
        
        # 记录到存储
        entry_id = self.store.add(
            error=f"{error_type}: {error_msg}",
            solution=solution,
            context=context,
            cause=self._analyze_cause(error, tb_str),
            tags=",".join(tags)
        )
        
        # 添加到索引以便快速检查重复
        self._recorded_hashes.add(error_hash)
        
        return entry_id
    
    def _suggest_solution(self, error: Exception, tb_str: str) -> str:
        """根据错误类型建议解决方案"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        suggestions = {
            "ModuleNotFoundError": f"pip install {error_msg.split(\"'\")[1] if \"'\" in error_msg else '模块名'}",
            "ImportError": "检查模块是否正确安装，或尝试重新安装",
            "FileNotFoundError": f"检查文件路径: {error_msg}",
            "PermissionError": "检查文件/目录权限，或以管理员权限运行",
            "KeyError": f"检查字典键是否存在: {error_msg}",
            "IndexError": "检查列表/数组索引是否越界",
            "AttributeError": f"检查对象是否有该属性: {error_msg}",
            "TypeError": "检查参数类型是否匹配",
            "ValueError": "检查参数值是否有效",
            "ZeroDivisionError": "避免除以零，添加检查逻辑",
            "ConnectionError": "检查网络连接和目标地址",
            "TimeoutError": "增加超时时间或检查服务是否可用",
        }
        
        if error_type in suggestions:
            return suggestions[error_type]
        
        return "查看错误堆栈，定位问题代码并修复"
    
    def _analyze_cause(self, error: Exception, tb_str: str) -> str:
        """分析错误根本原因"""
        lines = tb_str.strip().split("\n")
        
        # 提取最后调用的位置
        for line in reversed(lines):
            if "File \"" in line and "line" in line:
                return f"发生在: {line.strip()}"
        
        return ""
    
    def enable(self):
        """启用自动记录"""
        self._enabled = True
    
    def disable(self):
        """禁用自动记录"""
        self._enabled = False
    
    def add_auto_tag(self, tag: str):
        """添加自动标签"""
        self._auto_tags.append(tag)
    
    def add_skip_pattern(self, pattern: str):
        """添加跳过模式（正则表达式）"""
        self._skip_patterns.append(pattern)


# 全局记录器实例
_recorder = None

def get_recorder() -> AutoRecorder:
    """获取全局记录器实例"""
    global _recorder
    if _recorder is None:
        _recorder = AutoRecorder()
    return _recorder


# ============ 装饰器 ============

def auto_record(func: Optional[Callable] = None, *, 
                context: str = "",
                tags: List[str] = None,
                reraise: bool = True,
                silent: bool = False) -> Callable:
    """
    自动记录装饰器
    
    自动捕获函数中的异常并记录到知识库
    
    Args:
        context: 额外上下文描述
        tags: 额外标签
        reraise: 是否重新抛出异常（默认True）
        silent: 是否静默（不打印记录信息）
        
    用法:
        @auto_record
        def my_function():
            ...
            
        @auto_record(context="处理数据时", tags=["data"])
        def process_data():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            recorder = get_recorder()
            
            # 添加额外标签
            if tags:
                for tag in tags:
                    recorder.add_auto_tag(tag)
            
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # 记录错误
                entry_id = recorder.record(
                    error=e,
                    func_name=f.__name__,
                    extra_context=context
                )
                
                if entry_id and not silent:
                    print(f"[AutoRecord] 错误已自动记录: {entry_id}")
                
                if reraise:
                    raise
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


# ============ 上下文管理器 ============

@contextmanager
def auto_record_context(context: str = "", 
                        tags: List[str] = None,
                        silent: bool = False):
    """
    自动记录上下文管理器
    
    自动捕获代码块中的异常并记录
    
    Args:
        context: 上下文描述
        tags: 标签列表
        silent: 是否静默
        
    用法:
        with auto_record_context("处理用户数据"):
            process_user_data()
            
        with auto_record_context("API调用", tags=["api", "network"]):
            response = requests.get(url)
    """
    recorder = get_recorder()
    
    # 添加标签
    if tags:
        for tag in tags:
            recorder.add_auto_tag(tag)
    
    try:
        yield recorder
    except Exception as e:
        # 记录错误
        entry_id = recorder.record(
            error=e,
            extra_context=context
        )
        
        if entry_id and not silent:
            print(f"[AutoRecord] 错误已自动记录: {entry_id}")
        
        raise


# ============ 全局异常钩子 ============

class GlobalExceptionHook:
    """全局异常钩子，捕获所有未处理的异常"""
    
    def __init__(self):
        self._original_hook = None
        self._recorder = None
        self._enabled = False
    
    def install(self):
        """安装全局异常钩子"""
        if self._enabled:
            return
        
        self._original_hook = sys.excepthook
        sys.excepthook = self._handle_exception
        self._recorder = get_recorder()
        self._enabled = True
        print("[AutoRecord] 全局异常捕获已启用")
    
    def uninstall(self):
        """卸载全局异常钩子"""
        if not self._enabled:
            return
        
        sys.excepthook = self._original_hook
        self._enabled = False
        print("[AutoRecord] 全局异常捕获已禁用")
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理异常"""
        # 记录异常
        if self._recorder and exc_value:
            try:
                entry_id = self._recorder.record(
                    error=exc_value,
                    extra_context="未捕获的全局异常"
                )
                if entry_id:
                    print(f"[AutoRecord] 未捕获异常已记录: {entry_id}")
            except:
                pass  # 记录失败不影响正常异常处理
        
        # 调用原始钩子
        if self._original_hook:
            self._original_hook(exc_type, exc_value, exc_traceback)


# 全局钩子实例
_global_hook = None

def install_global_hook():
    """安装全局异常钩子"""
    global _global_hook
    if _global_hook is None:
        _global_hook = GlobalExceptionHook()
    _global_hook.install()

def uninstall_global_hook():
    """卸载全局异常钩子"""
    global _global_hook
    if _global_hook:
        _global_hook.uninstall()


# ============ 便捷函数 ============

def enable_auto_record():
    """启用自动记录"""
    get_recorder().enable()
    print("[AutoRecord] 自动记录已启用")

def disable_auto_record():
    """禁用自动记录"""
    get_recorder().disable()
    print("[AutoRecord] 自动记录已禁用")

def is_auto_record_enabled() -> bool:
    """检查自动记录是否启用"""
    return get_recorder()._enabled


def get_recent_auto_records(limit: int = 10) -> List[Dict]:
    """获取最近的自动记录"""
    store = get_store()
    return store.list_all(recent=limit)


# ============ 初始化 ============

def init_auto_record(enable_global_hook: bool = False,
                     auto_tags: List[str] = None):
    """
    初始化自动记录系统
    
    Args:
        enable_global_hook: 是否启用全局异常捕获
        auto_tags: 自动添加的标签
    """
    recorder = get_recorder()
    recorder.enable()
    
    if auto_tags:
        for tag in auto_tags:
            recorder.add_auto_tag(tag)
    
    if enable_global_hook:
        install_global_hook()
    
    print("[AutoRecord] 自动记录系统已初始化")
    return recorder


# 如果直接运行此脚本，执行测试
if __name__ == "__main__":
    # 初始化并启用全局捕获
    init_auto_record(enable_global_hook=True)
    
    # 使用装饰器的示例
    @auto_record(context="测试装饰器")
    def test_decorator():
        raise ValueError("测试装饰器错误捕获")
    
    # 使用上下文管理器的示例
    try:
        with auto_record_context("测试上下文管理器"):
            x = 1 / 0
    except:
        pass
    
    # 测试全局捕获
    # raise RuntimeError("测试全局捕获")
    
    print("\n自动记录测试完成")
