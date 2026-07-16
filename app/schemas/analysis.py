# app/schemas/analysis.py
from pydantic import BaseModel, Field
from typing import List, Optional


class TechEvidence(BaseModel):
    technology: str = Field(description="技术或组件名称")
    category: str = Field(description="所属类别，如语言、框架、存储、测试或部署")
    purpose: str = Field(description="它在项目中的实际用途")
    evidence: List[str] = Field(default_factory=list, description="能够证明判断的文件路径或代码符号")
    confidence: str = Field(default="medium", description="判断置信度：high、medium 或 low")


class DirectoryModule(BaseModel):
    path: str = Field(description="相对项目根目录的路径")
    role: str = Field(description="该目录或模块承担的职责")
    key_files: List[str] = Field(default_factory=list, description="最重要的文件")
    relationships: List[str] = Field(default_factory=list, description="与其他模块的调用或依赖关系")

class TechStackDetail(BaseModel):
    language: str = Field(description="项目使用的主要编程语言")
    framework: str = Field(description="核心 Web 或业务框架，如 Django, FastAPI, Vue 3")
    database: Optional[str] = Field(None, description="识别出的数据库，如 MySQL, Redis, PostgreSQL")
    tools: List[str] = Field(default_factory=list, description="其他工具或中间件，如 Docker, Nginx, Celery")
    frontend: List[str] = Field(default_factory=list, description="前端技术")
    backend: List[str] = Field(default_factory=list, description="后端与 API 技术")
    data_storage: List[str] = Field(default_factory=list, description="数据库、缓存、文件或对象存储")
    testing: List[str] = Field(default_factory=list, description="测试与质量工具")
    deployment: List[str] = Field(default_factory=list, description="构建、容器、CI/CD 与部署技术")
    evidence: List[TechEvidence] = Field(default_factory=list, description="技术判断及代码证据")

class ProjectSummaryResponse(BaseModel):
    background: str = Field(description="项目背景、目标用户与解决的问题")
    architecture_summary: str = Field(description="整体架构、模块边界和主要执行方式")
    core_features: List[str] = Field(description="列出项目实现的核心业务功能列表")
    entry_points: List[str] = Field(default_factory=list, description="入口文件、命令、路由或启动函数")
    directory_modules: List[DirectoryModule] = Field(default_factory=list, description="核心目录和模块职责")
    data_and_config: List[str] = Field(default_factory=list, description="配置、数据、状态及外部依赖说明")
    risks_and_notes: List[str] = Field(default_factory=list, description="从代码中能确认的风险、缺口或注意事项")
    tech_stack: TechStackDetail = Field(description="技术栈的详细细节")
