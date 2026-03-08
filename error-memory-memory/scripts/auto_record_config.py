#!/usr/bin/env python3
"""
自动记录配置文件管理
支持 JSON 和 Python 配置文件
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any


DEFAULT_CONFIG = {
    "version": "1.0",
    "enabled": True,
    "global_hook": False,
    "auto_tags": ["auto-recorded"],
    "skip_patterns": [
        "KeyboardInterrupt",
        "SystemExit",
        "pytest_",
        "unittest\\.",
        "test_",
        "_test.py"
    ],
    "error_solutions": {
        "ModuleNotFoundError": {
            "solution": "pip install {module}",
            "auto_extract": True,
            "extract_pattern": "'([^']+)'"
        },
        "ImportError": {
            "solution": "检查模块是否正确安装：pip install <模块名>",
            "auto_extract": False
        },
        "FileNotFoundError": {
            "solution": "检查文件路径是否正确: {path}",
            "auto_extract": True,
            "extract_pattern": "'(.*?)'"
        },
        "PermissionError": {
            "solution": "检查文件/目录权限，或以管理员权限运行",
            "auto_extract": False
        },
        "KeyError": {
            "solution": "检查字典中是否存在键: {key}",
            "auto_extract": True,
            "extract_pattern": "'(.*?)'"
        },
        "IndexError": {
            "solution": "检查列表/数组索引是否越界，使用 len() 确认长度",
            "auto_extract": False
        },
        "AttributeError": {
            "solution": "检查对象类型和属性名是否正确",
            "auto_extract": False
        },
        "TypeError": {
            "solution": "检查参数类型是否匹配，参考函数签名",
            "auto_extract": False
        },
        "ValueError": {
            "solution": "检查参数值是否在有效范围内",
            "auto_extract": False
        },
        "ZeroDivisionError": {
            "solution": "避免除以零，添加检查逻辑：if divisor != 0:",
            "auto_extract": False
        },
        "ConnectionError": {
            "solution": "检查网络连接和目标地址是否可访问",
            "auto_extract": False
        },
        "TimeoutError": {
            "solution": "增加超时时间或检查服务是否可用",
            "auto_extract": False
        },
        "JSONDecodeError": {
            "solution": "检查JSON格式是否正确，使用jsonlint验证",
            "auto_extract": False
        },
        "SyntaxError": {
            "solution": "检查Python语法，特别是括号匹配和缩进",
            "auto_extract": False
        },
        "IndentationError": {
            "solution": "检查缩进是否一致（空格 vs Tab）",
            "auto_extract": False
        },
        "NameError": {
            "solution": "检查变量/函数名是否拼写正确，或是否已定义",
            "auto_extract": True,
            "extract_pattern": "name '([^']+)'"
        },
        "RecursionError": {
            "solution": "检查递归终止条件，考虑使用循环替代",
            "auto_extract": False
        },
        "MemoryError": {
            "solution": "优化内存使用，考虑分批处理数据",
            "auto_extract": False
        },
        "OSError": {
            "solution": "检查系统资源和权限",
            "auto_extract": False
        },
        "RuntimeError": {
            "solution": "查看详细错误信息，检查程序状态",
            "auto_extract": False
        }
    },
    "smart_tagging": {
        "enabled": True,
        "error_type_tags": True,
        "module_tags": True,
        "function_prefix_tags": True
    },
    "deduplication": {
        "enabled": True,
        "time_window_minutes": 60,
        "similarity_threshold": 0.85
    },
    "output": {
        "print_on_record": True,
        "show_traceback_preview": True,
        "traceback_lines": 3
    }
}


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.skill_dir = Path(__file__).parent.parent
        self.config_file = self.skill_dir / "config" / "auto_record.json"
        self.config = None
        self._load()
    
    def _load(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # 合并默认配置
                self._merge_defaults()
            except Exception as e:
                print(f"[Config] 加载配置失败，使用默认配置: {e}")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
            self._save()
    
    def _merge_defaults(self):
        """合并默认配置（添加新字段）"""
        def merge_dict(base: dict, update: dict):
            for key, value in update.items():
                if key not in base:
                    base[key] = value
                elif isinstance(value, dict) and isinstance(base.get(key), dict):
                    merge_dict(base[key], value)
        
        merge_dict(self.config, DEFAULT_CONFIG)
    
    def _save(self):
        """保存配置"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save()
    
    def get_solution_template(self, error_type: str) -> Dict:
        """获取错误类型的解决方案模板"""
        return self.config.get("error_solutions", {}).get(error_type, {})
    
    def should_skip(self, error_type: str, error_msg: str) -> bool:
        """检查是否应该跳过此错误"""
        import re
        full_error = f"{error_type}: {error_msg}"
        
        for pattern in self.config.get("skip_patterns", []):
            try:
                if re.search(pattern, full_error):
                    return True
            except re.error:
                continue
        
        return False
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.config.get("enabled", True)
    
    def get_auto_tags(self) -> List[str]:
        """获取自动标签"""
        return self.config.get("auto_tags", [])
    
    def add_auto_tag(self, tag: str):
        """添加自动标签"""
        tags = self.config.get("auto_tags", [])
        if tag not in tags:
            tags.append(tag)
            self.set("auto_tags", tags)
    
    def remove_auto_tag(self, tag: str):
        """移除自动标签"""
        tags = self.config.get("auto_tags", [])
        if tag in tags:
            tags.remove(tag)
            self.set("auto_tags", tags)
    
    def add_skip_pattern(self, pattern: str):
        """添加跳过模式"""
        patterns = self.config.get("skip_patterns", [])
        if pattern not in patterns:
            patterns.append(pattern)
            self.set("skip_patterns", patterns)
    
    def reset(self):
        """重置为默认配置"""
        self.config = DEFAULT_CONFIG.copy()
        self._save()
    
    def show(self):
        """显示当前配置"""
        print(json.dumps(self.config, ensure_ascii=False, indent=2))


# 全局配置实例
_config_manager = None

def get_config() -> ConfigManager:
    """获取配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == "__main__":
    config = get_config()
    print("当前配置:")
    config.show()
