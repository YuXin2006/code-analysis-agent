
import os
import sys

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.file_utils import generate_tree_structure
from app.services.code_parser import CodeParserService
from app.services.data_flow import DataFlowService

if __name__ == "__main__":
    os.environ["LLM_API_KEY"] = "你的真实大模型API_KEY"
    current_project_path = os.path.dirname(os.path.abspath(__file__))
    # 往上回退一级到项目根目录进行分析
    root_path = os.path.dirname(current_project_path)
    
    print("正在提取本地文件...")
    tree_str = generate_tree_structure(root_path)
    code_ctx = CodeParserService.prepare_llm_context(root_path)
    
    print("正在连接大模型生成数据流与知识图谱，请稍候...")
    flow_service = DataFlowService()
    result = flow_service.analyze_data_flow_and_graph(tree_str, code_ctx)
    
    print("\n====== 1. Mermaid 数据流报告 ======")
    print(result["markdown_report"])
    
    print("\n====== 2. 知识图谱数据 (JSON) ======")
    print(result["graph_data"])