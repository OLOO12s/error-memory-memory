"""
错误记忆存储核心模块
提供数据存储、查询、更新等功能
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


@contextmanager
def file_lock(lock_path: Path, timeout: float = 5.0):
    """简易文件锁，防止多进程并发写入"""
    lock_file = lock_path.with_suffix(".lock")
    start = time.time()
    while True:
        try:
            # 使用 os.open 的 O_CREAT|O_EXCL 原子创建
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - start > timeout:
                # 超时: 可能是残留锁文件，强制清除
                try:
                    lock_file.unlink()
                except OSError:
                    pass
                continue
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            lock_file.unlink()
        except OSError:
            pass


class ErrorMemoryStore:
    """错误记忆存储类"""
    
    def __init__(self):
        # 获取skill目录路径
        self.skill_dir = Path(__file__).parent.parent
        self.memory_dir = self.skill_dir / "memory"
        self.index_file = self.memory_dir / "index.json"
        
        # 确保目录存在
        self.memory_dir.mkdir(exist_ok=True)
        
        # 加载或创建索引
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """加载索引文件"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "last_id": 0,
            "entries": [],
            "tags": {}
        }
    
    def _save_index(self):
        """保存索引文件（带文件锁）"""
        with file_lock(self.index_file):
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def _get_next_id(self) -> str:
        """生成下一个错误ID"""
        self.index["last_id"] += 1
        return f"ERR-{self.index['last_id']:03d}"
    
    def _save_entry(self, entry_id: str, data: Dict):
        """保存单条记录（带文件锁）"""
        entry_file = self.memory_dir / f"{entry_id}.json"
        with file_lock(entry_file):
            with open(entry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_entry(self, entry_id: str) -> Optional[Dict]:
        """加载单条记录"""
        entry_file = self.memory_dir / f"{entry_id}.json"
        if entry_file.exists():
            with open(entry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def add(self, error: str, solution: str, context: str = "", 
            cause: str = "", prevention: str = "", tags: str = "") -> str:
        """
        添加新错误记录
        
        Args:
            error: 错误描述
            solution: 解决方法
            context: 发生场景
            cause: 根本原因
            prevention: 预防措施
            tags: 标签（逗号分隔）
            
        Returns:
            新记录的ID
        """
        entry_id = self._get_next_id()
        now = datetime.now().isoformat()
        
        # 处理标签
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        entry = {
            "id": entry_id,
            "error": error,
            "context": context,
            "solution": solution,
            "cause": cause,
            "prevention": prevention,
            "tags": tag_list,
            "created_at": now,
            "updated_at": now,
            "hit_count": 0
        }
        
        # 保存记录
        self._save_entry(entry_id, entry)
        
        # 更新索引
        self.index["entries"].append({
            "id": entry_id,
            "error": error[:100],  # 简要描述
            "tags": tag_list,
            "created_at": now
        })
        
        # 更新标签索引
        for tag in tag_list:
            if tag not in self.index["tags"]:
                self.index["tags"][tag] = []
            self.index["tags"][tag].append(entry_id)
        
        self._save_index()
        
        return entry_id
    
    def get(self, entry_id: str) -> Optional[Dict]:
        """获取单条记录"""
        return self._load_entry(entry_id)
    
    def query(self, keyword: str = "", tags: List[str] = None,
              fuzzy: bool = False, limit: int = 10) -> List[Dict]:
        """
        查询记录

        Args:
            keyword: 关键词（支持空格分隔的多关键词 AND 搜索）
            tags: 标签列表
            fuzzy: 是否模糊匹配（搜索所有字段 vs 仅 error/context/tags）
            limit: 返回数量限制

        Returns:
            匹配的记录列表
        """
        results = []
        # 支持多关键词: "blender render error" → ["blender", "render", "error"]
        keywords = [k.lower() for k in keyword.split() if k.strip()] if keyword else []

        for entry_info in self.index["entries"]:
            entry = self._load_entry(entry_info["id"])
            if not entry:
                continue

            # 标签筛选
            if tags:
                if not any(tag in entry["tags"] for tag in tags):
                    continue

            # 关键词匹配
            if keywords:
                # fuzzy=True 搜索所有字段，否则只搜索 error/context/tags
                if fuzzy:
                    text_to_search = " ".join([
                        entry.get("error", ""),
                        entry.get("context", ""),
                        entry.get("solution", ""),
                        entry.get("cause", ""),
                        " ".join(entry.get("tags", []))
                    ]).lower()
                else:
                    text_to_search = " ".join([
                        entry.get("error", ""),
                        entry.get("context", ""),
                        " ".join(entry.get("tags", []))
                    ]).lower()

                # 所有关键词都必须匹配 (AND)
                if all(kw in text_to_search for kw in keywords):
                    entry_copy = entry.copy()
                    entry_copy["_score"] = sum(
                        text_to_search.count(kw) for kw in keywords
                    )
                    results.append(entry_copy)
            else:
                results.append(entry)

        # 有关键词时按得分排序，否则按时间
        if keywords:
            results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        else:
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return results[:limit]
    
    def list_all(self, tag: str = "", by_hits: bool = False, 
                 recent: int = 0) -> List[Dict]:
        """
        列出所有记录
        
        Args:
            tag: 按标签筛选
            by_hits: 按使用频率排序
            recent: 只显示最近N条
            
        Returns:
            记录列表
        """
        results = []
        
        # 获取所有记录
        entries_to_load = self.index["entries"]
        if tag:
            entry_ids = self.index.get("tags", {}).get(tag, [])
            entries_to_load = [e for e in entries_to_load if e["id"] in entry_ids]
        
        for entry_info in entries_to_load:
            entry = self._load_entry(entry_info["id"])
            if entry:
                results.append(entry)
        
        # 排序
        if by_hits:
            results.sort(key=lambda x: x.get("hit_count", 0), reverse=True)
        else:
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 限制数量
        if recent > 0:
            results = results[:recent]
        
        return results
    
    def update(self, entry_id: str, **kwargs) -> bool:
        """
        更新记录
        
        Args:
            entry_id: 记录ID
            **kwargs: 要更新的字段
            
        Returns:
            是否成功
        """
        entry = self._load_entry(entry_id)
        if not entry:
            return False
        
        # 特殊处理某些字段
        if "add_tags" in kwargs:
            new_tags = [t.strip() for t in kwargs.pop("add_tags").split(",") if t.strip()]
            entry["tags"].extend(new_tags)
            entry["tags"] = list(set(entry["tags"]))  # 去重
            
            # 更新标签索引
            for tag in new_tags:
                if tag not in self.index["tags"]:
                    self.index["tags"][tag] = []
                if entry_id not in self.index["tags"][tag]:
                    self.index["tags"][tag].append(entry_id)
        
        if "hit" in kwargs:
            entry["hit_count"] = entry.get("hit_count", 0) + 1
            del kwargs["hit"]
        
        # 更新其他字段
        valid_fields = ["error", "context", "solution", "cause", "prevention"]
        for field, value in kwargs.items():
            if field in valid_fields:
                entry[field] = value
        
        entry["updated_at"] = datetime.now().isoformat()
        
        # 保存
        self._save_entry(entry_id, entry)
        self._save_index()
        
        return True
    
    def delete(self, entry_id: str) -> bool:
        """删除记录"""
        entry_file = self.memory_dir / f"{entry_id}.json"
        if entry_file.exists():
            entry_file.unlink()

            # 更新索引
            self.index["entries"] = [e for e in self.index["entries"] if e["id"] != entry_id]

            # 更新标签索引并清除空数组
            tags_to_remove = []
            for tag in self.index.get("tags", {}):
                self.index["tags"][tag] = [e for e in self.index["tags"][tag] if e != entry_id]
                if not self.index["tags"][tag]:
                    tags_to_remove.append(tag)
            for tag in tags_to_remove:
                del self.index["tags"][tag]

            self._save_index()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.index["entries"])
        tags = {tag: len(entries) for tag, entries in self.index.get("tags", {}).items()}
        
        # 计算总命中次数
        total_hits = 0
        for entry_info in self.index["entries"]:
            entry = self._load_entry(entry_info["id"])
            if entry:
                total_hits += entry.get("hit_count", 0)
        
        return {
            "total_entries": total,
            "total_tags": len(tags),
            "total_hits": total_hits,
            "tag_distribution": tags
        }


# 单例模式
_store = None

def get_store() -> ErrorMemoryStore:
    """获取存储实例（单例）"""
    global _store
    if _store is None:
        _store = ErrorMemoryStore()
    return _store
