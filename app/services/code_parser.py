# app/services/code_parser.py
from pathlib import Path
from typing import Dict, List
from app.utils.file_utils import should_ignore

class CodeParserService:
    @staticmethod
    def load_project_files(project_path: str) -> List[Dict[str, str]]:
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
                    # 读取文本内容（使用 utf-8，出错时忽略，防止遇到二进制文件崩溃）
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    
                    # 获取相对路径作为文件的唯一标识
                    relative_path = str(path.relative_to(root))
                    
                    project_files.append({
                        "file_path": relative_path,
                        "content": content
                    })
                except Exception as e:
                    # 可以在这里记录日志，比如遇到无法读取的文件
                    print(f"无法读取文件 {path}: {str(e)}")
                    
        return project_files

    @staticmethod
    def prepare_llm_context(project_path: str) -> str:
        """
        将整个代码库组装成一个格式化的字符串，供 LLM 分析
        """
        files_data = CodeParserService.load_project_files(project_path)
        
        context_blocks = []
        for file_info in files_data:
            block = (
                f"--- 开始文件: {file_info['file_path']} ---\n"
                f"{file_info['content']}\n"
                f"--- 结束文件: {file_info['file_path']} ---\n"
            )
            context_blocks.append(block)
            
        return "\n".join(context_blocks)