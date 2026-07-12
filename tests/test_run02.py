# test_run.py
import os
import sys
from pathlib import Path

# 将项目根目录加入 Python 路径，防止在 tests 目录下运行时报导入错误
current_dir = Path(__file__).resolve().parent
if current_dir.name == "tests":
    root_path = current_dir.parent
else:
    root_path = current_dir
sys.path.append(str(root_path))

from app.core.config import settings
from app.utils.file_utils import generate_tree_structure
from app.services.code_parser import CodeParserService
from app.services.tech_detector import TechDetectorService
from app.services.data_flow import DataFlowService
from app.services.visualizer import VisualizerService

def run_agent_pipeline(target_project_path: str):
    """
    运行完整的 Agent 分析与可视化渲染流水线
    """
    target_path = Path(target_project_path).resolve()
    if not target_path.exists():
        print(f"❌ 错误: 目标路径不存在 -> {target_path}")
        return

    print(f"==================================================")
    print(f"🚀 开始分析目标项目: {target_path.name}")
    print(f"📍 项目绝对路径: {target_path}")
    print(f"==================================================")

    # 1. 数据摄入层：提取文件结构和源码上下文
    print("1/4 [数据摄入] 正在扫描文件并构建代码上下文...")
    tree_str = generate_tree_structure(str(target_path))
    code_ctx = CodeParserService.prepare_llm_context(str(target_path))
    
    if not code_ctx.strip():
        print("⚠️ 警告: 未在该目录下扫描到有效的合规文本代码文件！")
        return

    # 2. 分析推理层 - 阶段 A：技术栈与背景提取
    print("2/4 [AI 分析] 正在连接大模型识别技术栈与业务背景...")
    detector = TechDetectorService()
    # 动态利用提取出的上下文进行分析
    summary_result = detector.llm_client.analyze_project_summary(tree_str, code_ctx)

    # 3. 分析推理层 - 阶段 B：数据流向与知识图谱关系抽取
    print("3/4 [AI 分析] 正在深度挖掘数据流向并构建实体关系网...")
    flow_service = DataFlowService()
    flow_graph_result = flow_service.analyze_data_flow_and_graph(tree_str, code_ctx)

    # 4. 表现层：利用渲染引擎输出美化后的 HTML 报告
    print("4/4 [可视化渲染] 正在将分析数据注入模板并美化排版...")
    visualizer = VisualizerService(template_dir=str(root_path / "app/templates"))
    
    # 确保输出缓存目录存在
    output_dir = root_path / "data/cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_html_path = output_dir / f"{target_path.name}_analysis_report.html"
    
    # 转换 Pydantic 模型为字典供 Jinja2 渲染
    summary_dict = summary_result.model_dump()
    
    visualizer.generate_html_report(summary_dict, flow_graph_result, str(output_html_path))
    
    print(f"==================================================")
    print(f"🎉 分析圆满完成！")
    print(f"📊 请双击或将以下文件拖入浏览器查看精美报告：")
    print(f"👉 {output_html_path}")
    print(f"==================================================")

if __name__ == "__main__":

    TARGET_PROJECT = str(root_path)
  
    run_agent_pipeline(TARGET_PROJECT)