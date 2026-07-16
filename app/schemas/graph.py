# app/schemas/graph.py
from pydantic import BaseModel, Field
from typing import List, Literal

class GraphNode(BaseModel):
    id: str = Field(description="节点唯一标识，可以是文件名、类名或函数名，例如 'main.py' 或 'CodeParserService'")
    type: Literal["file", "class", "function"] = Field(description="节点类型")
    label: str = Field(default="", description="适合图中显示的简短名称")
    description: str = Field(default="", description="节点职责的一句话说明")

class GraphEdge(BaseModel):
    source: str = Field(description="关系的源节点 id")
    target: str = Field(description="关系的目标节点 id")
    relation: str = Field(description="依赖关系类型，例如: imports, calls, defines")

class CodeGraphData(BaseModel):
    nodes: List[GraphNode] = Field(description="代码库中的核心实体节点列表")
    edges: List[GraphEdge] = Field(description="实体之间的关联边列表")


class FlowNode(BaseModel):
    id: str = Field(description="简单且唯一的节点标识")
    label: str = Field(description="不超过 16 个汉字的显示文本")
    type: Literal["input", "process", "storage", "output", "external"] = "process"


class FlowEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class FlowGraphData(BaseModel):
    nodes: List[FlowNode]
    edges: List[FlowEdge]


class FlowStage(BaseModel):
    title: str
    description: str
    input: str = ""
    output: str = ""


class FlowAnalysisResponse(BaseModel):
    overview: str
    stages: List[FlowStage]
    flowchart_data: FlowGraphData
    observations: List[str] = Field(default_factory=list)
