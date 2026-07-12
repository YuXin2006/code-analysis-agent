# app/services/llm_client.py
import json
from openai import OpenAI
from app.core.config import settings
from app.schemas.analysis import ProjectSummaryResponse

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    def analyze_project_summary(self, tree_structure: str, code_context: str) -> ProjectSummaryResponse:
        """
        将目录结构和核心代码发给 LLM，要求其返回结构化的背景和技术栈分析
        """
        system_prompt = (
            "你是一个顶级的全栈架构师和代码分析专家。你的任务是分析用户提供的代码库，"
            "理解其业务背景、核心功能和技术栈。\n"
            "你必须严格按照以下 JSON Schema 返回结果，不能添加任何额外字段：\n"
            "{\n"
            "  \"background\": \"项目背景描述（一句话或简短段落）\",\n"
            "  \"core_features\": [\"功能1\", \"功能2\", ...],\n"
            "  \"tech_stack\": {\n"
            "    \"language\": \"主要编程语言\",\n"
            "    \"framework\": \"核心框架\",\n"
            "    \"database\": \"数据库（可选）\",\n"
            "    \"tools\": [\"工具1\", \"工具2\", ...]\n"
            "  }\n"
            "}\n"
            "请确保返回的 JSON 字符串符合 JSON Schema 规范。所有内容使用中文。"
        )
        
        user_content = (
            f"以下是项目的目录结构：\n{tree_structure}\n\n"
            f"以下是项目核心文件的内容上下文：\n{code_context}\n\n"
            f"请按照指定的 JSON Schema 格式分析这个项目。"
        )

        # 利用 OpenAI/DeepSeek 的 json_object 模式或 tools 模式
        # 这里使用 JSON Mode 确保返回合规 JSON
        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}, 
            temperature=0.2 # 低随机性，保证分析准确
        )

        result_text = response.choices[0].message.content
        # 将 JSON 字符串解析并校验为 Pydantic 模型
        return ProjectSummaryResponse.model_validate(json.loads(result_text))