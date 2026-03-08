#!/usr/bin/env python3
"""
错误记忆与解决系统 - 自动记录模块

提供以下主要功能：
1. auto_record - 装饰器，自动捕获和记录函数异常
2. auto_record_block - 上下文管理器，自动记录代码块异常
3. init - 初始化自动记录系统
4. get_manager - 获取自动记录管理器

快速开始：
    from scripts import auto_record, init
    
    # 初始化
    init(enable_global=True)
    
    # 使用装饰器
    @auto_record
    def my_function():
        ...
"""

# 从 auto_record_v2 导入主要功能
try:
    from .auto_record_v2 import (
        auto_record,
        auto_record_block,
        init,
        get_manager,
        get_recorder,  # 向后兼容
        enable_auto_record,
        disable_auto_record,
        is_auto_record_enabled,
    )
    
    # 配置相关
    from .auto_record_config import get_config
    
    # 存储相关
    from .memory_store import get_store
    
    __all__ = [
        'auto_record',
        'auto_record_block',
        'init',
        'get_manager',
        'get_config',
        'get_store',
        'enable_auto_record',
        'disable_auto_record',
        'is_auto_record_enabled',
    ]
    
except ImportError as e:
    # 如果导入失败，提供友好的错误信息
    print(f"[ErrorMemory] 导入警告: {e}")
    print("[ErrorMemory] 某些功能可能不可用")
    
    __all__ = []

__version__ = "2.0.0"
