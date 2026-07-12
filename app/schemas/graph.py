# app/schemas/graph.py
from pydantic import BaseModel, Field
from typing import List

class GraphNode(BaseModel):
    id: str = Field(description="节点唯一标识，可以是文件名、类名或函数名，例如 'main.py' 或 'CodeParserService'")
    type: str = Field(description="节点类型，只能是以下之一: file, class, function")

class GraphEdge(BaseModel):
    source: str = Field(description="关系的源节点 id")
    target: str = Field(description="关系的目标节点 id")
    relation: str = Field(description="依赖关系类型，例如: imports, calls, defines")

class CodeGraphData(BaseModel):
    nodes: List[GraphNode] = Field(description="代码库中的核心实体节点列表")
    edges: List[GraphEdge] = Field(description="实体之间的关联边列表")