# app/services/llm_client.py
import json
import re
from typing import Any, Dict, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.schemas.analysis import ProjectSummaryResponse


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    @staticmethod
    def _extract_json_text(raw_text: str) -> str:
        text = (raw_text or "").strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("大模型未返回完整 JSON 对象")
        return text[start:end + 1]

    @classmethod
    def parse_json_object(cls, raw_text: str) -> Dict[str, Any]:
        """解析模型 JSON，并本地修正常见的尾逗号问题。"""
        candidate = cls._extract_json_text(raw_text)
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError as first_error:
            # 只做确定性较高的修复；缺逗号、断句等问题交给模型重试。
            without_trailing_commas = re.sub(r",\s*([}\]])", r"\1", candidate)
            if without_trailing_commas != candidate:
                try:
                    return json.loads(without_trailing_commas, strict=False)
                except json.JSONDecodeError:
                    pass
            raise first_error

    def request_validated_json(
        self,
        system_prompt: str,
        user_content: str,
        response_model: Type[SchemaT],
        temperature: float = 0.1,
    ) -> SchemaT:
        """请求、修复并校验结构化输出，最多自动尝试三次。"""
        max_attempts = max(1, getattr(settings, "LLM_JSON_MAX_ATTEMPTS", 3))
        max_tokens = getattr(settings, "LLM_MAX_OUTPUT_TOKENS", 8192)
        last_raw = ""
        last_error: Exception | None = None
        last_finish_reason = ""

        for attempt in range(max_attempts):
            if attempt == 0:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
                current_temperature = temperature
            elif last_raw and last_finish_reason != "length":
                # 完整但语法/Schema 不合法时，只修复上一份 JSON，避免再次处理大型代码上下文。
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "你是 JSON 修复器。只修复输入中的 JSON 语法和字段类型，"
                            "不得添加 Markdown，不得解释，不得删除顶层字段。"
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"上一响应校验失败：{last_error}\n\n"
                            "请返回修复后的单个 JSON 对象：\n"
                            f"{last_raw}"
                        )
                    }
                ]
                current_temperature = 0.0
            else:
                # 如果上一响应被截断，重新基于原材料生成更精简的完整 JSON。
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                    {
                        "role": "user",
                        "content": (
                            "上一响应未形成完整合法 JSON。请重新生成更精简的版本："
                            "目录模块不超过 8 个，技术证据不超过 12 条，每段描述避免重复。"
                            "只返回一个完整 JSON 对象。"
                        )
                    }
                ]
                current_temperature = 0.0

            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=current_temperature,
                max_tokens=max_tokens
            )
            choice = response.choices[0]
            last_raw = choice.message.content or ""
            last_finish_reason = str(getattr(choice, "finish_reason", "") or "")

            try:
                if last_finish_reason == "length":
                    raise ValueError(
                        f"模型输出达到 max_tokens={max_tokens}，JSON 被截断"
                    )
                payload = self.parse_json_object(last_raw)
                return response_model.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc
                if attempt + 1 < max_attempts:
                    print(
                        f"⚠️ 大模型 JSON 第 {attempt + 1}/{max_attempts} 次校验失败，"
                        f"正在自动修复：{exc}"
                    )

        raise RuntimeError(
            f"大模型连续 {max_attempts} 次未返回合法的 {response_model.__name__}；"
            f"最后错误：{last_error}"
        ) from last_error

    def analyze_project_summary(
        self,
        tree_structure: str,
        code_context: str
    ) -> ProjectSummaryResponse:
        """基于目录全景和精选源码生成可追溯的技术架构分析。"""
        system_prompt = """
你是一名严谨的软件架构审计专家。请根据目录树与代码证据生成中文项目分析。

分析原则：
1. 先用目录树理解仓库边界，再结合清单、入口、配置和核心源码交叉验证。
2. 不要因为正文未收录某文件就断言它不存在；不要猜测代码中没有证据的技术。
3. 技术判断必须尽量给出文件路径或代码符号作为 evidence。
4. directory_modules 选择 4～8 个重要模块；tech_stack.evidence 不超过 12 条。
5. background 与 architecture_summary 各写 100～220 个汉字；核心功能写 4～8 项。
6. 字符串中的双引号必须正确转义。输出充分但避免空话、重复和过度展开。

严格只返回一个 JSON 对象，字段如下：
{
  "background": "项目目标、用户/场景以及解决的问题",
  "architecture_summary": "分层、模块边界、入口和主要执行路径",
  "core_features": ["功能及其实现落点"],
  "entry_points": ["路径或符号：用途"],
  "directory_modules": [
    {"path": "目录/模块", "role": "职责", "key_files": ["文件"], "relationships": ["依赖关系"]}
  ],
  "data_and_config": ["配置、数据、状态、外部服务说明"],
  "risks_and_notes": ["仅基于现有代码能确认的风险或缺口"],
  "tech_stack": {
    "language": "主要语言及大致角色",
    "framework": "核心框架；无证据则写 未识别",
    "database": "数据库/缓存；无证据时为 null",
    "tools": ["重要工具"],
    "frontend": ["前端技术"],
    "backend": ["后端/API 技术"],
    "data_storage": ["持久化、缓存或文件存储"],
    "testing": ["测试与质量工具"],
    "deployment": ["构建、容器、CI/CD、部署"],
    "evidence": [
      {"technology": "名称", "category": "类别", "purpose": "项目内用途", "evidence": ["路径/符号"], "confidence": "high|medium|low"}
    ]
  }
}
""".strip()

        user_content = (
            "# 项目目录树\n"
            f"{tree_structure}\n\n"
            "# 精选代码上下文\n"
            f"{code_context}\n\n"
            "请按照指定 JSON 结构完成分析。"
        )

        return self.request_validated_json(
            system_prompt=system_prompt,
            user_content=user_content,
            response_model=ProjectSummaryResponse,
            temperature=0.1
        )
