# app/utils/file_utils.py
import os
from pathlib import Path
from typing import List, Set
from app.core.config import settings

# 定义默认需要忽略的文件夹和文件后缀
DEFAULT_IGNORE_DIRS: Set[str] = {
    '.git', '.svn', 'node_modules', '__pycache__', 'venv', 
    '.venv', 'env', 'dist', 'build', '.idea', '.vscode', '.eggs',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'coverage', '.next',
    '.nuxt', 'target', 'vendor', 'data/temp'
}

SENSITIVE_NAMES: Set[str] = {
    '.env', '.env.local', '.env.production', '.env.development',
    'id_rsa', 'id_ed25519', 'credentials.json', 'secrets.json'
}

DEFAULT_IGNORE_EXTS: Set[str] = {
    '.pyc', '.pyo', '.pyd', '.png', '.jpg', '.jpeg', '.gif', 
    '.ico', '.svg', '.mp4', '.mp3', '.zip', '.tar', '.gz', 
    '.exe', '.dll', '.so', '.dylib', '.woff', '.woff2', '.eot', '.ttf'
}

def should_ignore(path: Path, root_dir: Path) -> bool:
    """
    判断当前路径是否应该被忽略
    """
    # 检查路径中的任何一级目录是否在忽略列表中
    try:
        relative_parts = path.relative_to(root_dir).parts
        for part in relative_parts:
            if part in DEFAULT_IGNORE_DIRS:
                return True
    except ValueError:
        pass
        
    # 检查文件后缀
    if path.name.lower() in SENSITIVE_NAMES:
        return True

    if path.is_file() and path.suffix.lower() in DEFAULT_IGNORE_EXTS:
        return True
        
    return False

def generate_tree_structure(root_path: str, max_depth: int | None = None,
                            max_entries: int | None = None) -> str:
    """
    生成项目的目录树文本结构（用于提供给 LLM 鸟瞰项目架构）
    示例输出：
    demo-project/
      main.py
      utils/
        helper.py
    """
    root = Path(root_path)
    tree_lines = [f"{root.name}/"]
    # 与旧版 config.py 兼容，避免只更新部分文件时发生 AttributeError。
    max_depth = max_depth or getattr(settings, "TREE_MAX_DEPTH", 8)
    max_entries = max_entries or getattr(settings, "TREE_MAX_ENTRIES", 2_000)
    entry_count = 0
    
    def _build_tree(current_dir: Path, prefix: str = "", depth: int = 0):
        nonlocal entry_count
        if depth >= max_depth:
            tree_lines.append(f"{prefix}└── …（已达到目录深度上限）")
            return
        # 获取当前目录下所有未被忽略的项，并排序（文件夹在前，文件在后）
        try:
            items = sorted(
                [item for item in current_dir.iterdir() if not should_ignore(item, root)],
                key=lambda x: (not x.is_dir(), x.name.lower())
            )
        except PermissionError:
            return

        count = len(items)
        for i, item in enumerate(items):
            if entry_count >= max_entries:
                tree_lines.append(f"{prefix}└── …（其余条目已省略）")
                return
            entry_count += 1
            is_last = (i == count - 1)
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                tree_lines.append(f"{prefix}{connector}{item.name}/")
                # 递归子目录
                next_prefix = prefix + ("    " if is_last else "│   ")
                _build_tree(item, next_prefix, depth + 1)
            else:
                tree_lines.append(f"{prefix}{connector}{item.name}")

    _build_tree(root)
    return "\n".join(tree_lines)
