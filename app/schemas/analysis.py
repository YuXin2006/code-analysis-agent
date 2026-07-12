# app/schemas/analysis.py
from pydantic import BaseModel, Field
from typing import List, Optional

class TechStackDetail(BaseModel):
    language: str = Field(description="项目使用的主要编程语言")
    framework: str = Field(description="核心 Web 或业务框架，如 Django, FastAPI, Vue 3")
    database: Optional[str] = Field(None, description="识别出的数据库，如 MySQL, Redis, PostgreSQL")
    tools: List[str] = Field(default=[], description="其他工具或中间件，如 Docker, Nginx, Celery")

class ProjectSummaryResponse(BaseModel):
    background: str = Field(description="项目的背景知识和存在目的（一句话或简短段落）")
    core_features: List[str] = Field(description="列出项目实现的核心业务功能列表")
    tech_stack: TechStackDetail = Field(description="技术栈的详细细节")