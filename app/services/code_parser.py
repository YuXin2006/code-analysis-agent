# app/services/code_parser.py
from pathlib import Path
from typing import Dict, List
from app.utils.file_utils import should_ignore
from app.core.config import settings


TEXT_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.vue', '.java', '.kt', '.go', '.rs',
    '.c', '.h', '.cpp', '.hpp', '.cs', '.php', '.rb', '.swift', '.scala', '.sql',
    '.html', '.css', '.scss', '.less', '.md', '.rst', '.txt', '.json', '.toml',
    '.yaml', '.yml', '.ini', '.cfg', '.xml', '.gradle', '.sh', '.bat', '.ps1'
}
PRIORITY_NAMES = {
    'readme.md', 'pyproject.toml', 'requirements.txt', 'package.json',
    'dockerfile', 'docker-compose.yml', 'docker-compose.yaml', 'pom.xml',
    'build.gradle', 'cargo.toml', 'go.mod', 'main.py', 'app.py', 'manage.py'
}

class CodeParserService:
    @staticmethod
    def load_project_files(project_path: str) -> List[Dict[str, object]]:
        """
        加载项目中所有合规文本文件的内容
        返回结构：[{"file_path": "app/main.py", "content": "..."}]
        """
        root = Path(project_path)
        project_files = []
        
        # 递归遍历所有文件
        for path in root.rglob('*'):
            if path.is_file() and not should_ignore(path, root):
                try:
                    if path.suffix.lower() not in TEXT_EXTENSIONS and path.name.lower() not in PRIORITY_NAMES:
                        continue
                    if path.stat().st_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                        continue
                    # 读取文本内容（使用 utf-8，出错时忽略，防止遇到二进制文件崩溃）
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    
                    # 获取相对路径作为文件的唯一标识
                    relative_path = str(path.relative_to(root))
                    
                    project_files.append({
                        "file_path": relative_path,
                        "content": content,
                        "size": len(content),
                        "priority": CodeParserService._priority(relative_path)
                    })
                except Exception as e:
                    # 可以在这里记录日志，比如遇到无法读取的文件
                    print(f"无法读取文件 {path}: {str(e)}")
                    
        return project_files

    @staticmethod
    def _priority(relative_path: str) -> int:
        path = Path(relative_path)
        name = path.name.lower()
        score = 0
        if name in PRIORITY_NAMES:
            score += 100
        if any(part.lower() in {'src', 'app', 'server', 'api', 'core', 'services'} for part in path.parts):
            score += 30
        if path.suffix.lower() in {'.py', '.ts', '.tsx', '.js', '.jsx', '.java', '.go', '.rs'}:
            score += 20
        score -= len(path.parts)
        return score

    @staticmethod
    def prepare_llm_context(project_path: str) -> str:
        """
        将整个代码库组装成一个格式化的字符串，供 LLM 分析
        """
        # 使用 getattr 提供向后兼容：即使用户只替换了本文件、尚未同步
        # config.py，也不会因为缺少新增配置项而直接中断。
        max_context_files = getattr(settings, "MAX_CONTEXT_FILES", 160)
        max_context_chars = getattr(settings, "MAX_CONTEXT_CHARS", 180_000)
        max_chars_per_file = getattr(settings, "MAX_CHARS_PER_FILE", 18_000)

        files_data = CodeParserService.load_project_files(project_path)
        files_data.sort(key=lambda item: (-item["priority"], item["file_path"].lower()))
        
        context_blocks = [
            "# 代码上下文说明",
            f"共发现 {len(files_data)} 个可分析文本文件；以下按入口、清单、核心源码优先排列。",
            "被截断或未纳入正文的文件仍会出现在目录树中，请勿据此断言其不存在。"
        ]
        used_chars = sum(len(block) for block in context_blocks)
        included = 0
        truncated_files = []
        for file_info in files_data:
            if included >= max_context_files or used_chars >= max_context_chars:
                break
            content = file_info['content']
            if len(content) > max_chars_per_file:
                content = content[:max_chars_per_file] + "\n…（该文件后续内容已截断）"
                truncated_files.append(file_info['file_path'])
            block = (
                f"--- 开始文件: {file_info['file_path']} ---\n"
                f"{content}\n"
                f"--- 结束文件: {file_info['file_path']} ---\n"
            )
            remaining = max_context_chars - used_chars
            if remaining < 600:
                break
            if len(block) > remaining:
                block = block[:remaining] + "\n…（上下文总长度达到上限）"
            context_blocks.append(block)
            used_chars += len(block)
            included += 1

        context_blocks.insert(3, f"实际纳入 {included} 个文件，单文件截断 {len(truncated_files)} 个。")
        return "\n".join(context_blocks)
