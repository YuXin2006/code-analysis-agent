# app/services/data_flow.py
import json
from app.services.llm_client import LLMClient
from app.schemas.graph import CodeGraphData
from app.core.config import settings

class DataFlowService:
    def __init__(self):
        self.llm_client = LLMClient()  

    def analyze_data_flow_and_graph(self, tree_structure: str, code_context: str):
        """
        分析代码库的数据流向，并提取知识图谱
        """
        # --- 任务 1：生成数据流与 Mermaid 脚本 ---
        flow_prompt = (
            "你是一个资深的系统架构师。请阅读提供的项目目录结构和代码，完成两件事：\n"
            "1. 用文字详细描述这个项目的数据流向（例如：用户请求是如何从入口进入，经过哪些服务，最终如何输出）。\n"
            "2. 使用 Mermaid 语法（graph TD 或 sequenceDiagram）绘制一张核心业务的数据流程图。\n\n"
            "不要返回任何 JSON，直接返回 Markdown 格式的报告，Mermaid 代码请包含在 ```mermaid 块中。"
        )
        
        user_content = f"目录结构：\n{tree_structure}\n\n核心代码：\n{code_context}"
        
        # 请求大模型生成 Markdown + Mermaid
        flow_response = self.llm_client.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": flow_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3
        )
        markdown_report = flow_response.choices[0].message.content

        # --- 任务 2：提取结构化的知识图谱 ---
        graph_prompt = (
            "你是一个静态代码分析专家。请分析代码中的文件、类、函数之间的调用和依赖关系。\n"
            "抽取最核心的节点和边，并严格按照以下 JSON Schema 格式返回：\n"
            "{\n"
            "  \"nodes\": [{\"id\": \"节点标识\", \"type\": \"file|class|function\"}, ...],\n"
            "  \"edges\": [{\"source\": \"源节点id\", \"target\": \"目标节点id\", \"relation\": \"imports|calls|defines\"}, ...]\n"
            "}\n"
            "注意：edges 必须包含 source、target、relation 三个字段，relation 只能是 imports、calls 或 defines 之一。\n"
            "不要包含任何 Markdown 标记或多余解释，只返回纯 JSON。"
        )
        
        graph_response = self.llm_client.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": graph_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        graph_json = json.loads(graph_response.choices[0].message.content)
        graph_data = CodeGraphData.model_validate(graph_json)
        
        return {
            "markdown_report": markdown_report,
            "graph_data": graph_data.model_dump()
        }