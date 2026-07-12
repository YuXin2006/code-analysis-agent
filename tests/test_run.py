# test_run.py
import os
import sys

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tech_detector import TechDetectorService

if __name__ == "__main__":
    # 在环境变量中设置你的 Key（或者直接写在 app/core/config.py 里）
    os.environ["LLM_API_KEY"] = "你的真实大模型API_KEY"
    
    # 让 Agent 分析它自己这个项目
    current_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    detector = TechDetectorService()
    result = detector.execute_analysis(current_project_path)
    
    print("\n====== Agent 分析结果 ======")
    print(f"项目背景: {result.background}")
    print(f"核心功能: {result.core_features}")
    print(f"技术栈语言: {result.tech_stack.language}")
    print(f"技术栈框架: {result.tech_stack.framework}")
    print(f"识别到的工具: {result.tech_stack.tools}")