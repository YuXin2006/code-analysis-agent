# app/services/tech_detector.py
from app.services.code_parser import CodeParserService
from app.utils.file_utils import generate_tree_structure
from app.services.llm_client import LLMClient
from app.schemas.analysis import ProjectSummaryResponse

class TechDetectorService:
    def __init__(self):
        self.llm_client = LLMClient()

    def execute_analysis(self, project_path: str) -> ProjectSummaryResponse:
        """统一构造目录全景和受控代码上下文，避免两者相互矛盾。"""
        tree_str = generate_tree_structure(project_path)
        
        # 2. 提取代码上下文
        code_ctx = CodeParserService.prepare_llm_context(project_path)
        
        # 3. 调用大模型进行深度理解
        print("正在基于目录全景和精选核心代码生成架构分析，请稍候...")
        analysis_result = self.llm_client.analyze_project_summary(tree_str, code_ctx)
        
        return analysis_result
