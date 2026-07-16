# app/services/data_flow.py
from app.schemas.graph import (
    CodeGraphData,
    FlowAnalysisResponse,
    FlowGraphData,
)
from app.services.llm_client import LLMClient


class DataFlowService:
    def __init__(self):
        self.llm_client = LLMClient()

    @staticmethod
    def _clean_label(value: str, limit: int = 36) -> str:
        value = " ".join(str(value or "").split())
        for char in ('"', "'", "`", "[", "]", "{", "}", "<", ">", "|", "\\"):
            value = value.replace(char, "")
        return value[:limit] or "未命名"

    @classmethod
    def _normalize_flow(cls, graph: FlowGraphData) -> FlowGraphData:
        """限制图规模并剔除悬空边，保证页面和 PDF 中都易读。"""
        nodes, seen = [], set()
        for node in graph.nodes[:10]:
            if node.id in seen:
                continue
            seen.add(node.id)
            node.label = cls._clean_label(node.label, 18)
            nodes.append(node)
        edges = [edge for edge in graph.edges if edge.source in seen and edge.target in seen][:14]
        for edge in edges:
            edge.label = cls._clean_label(edge.label, 12) if edge.label else ""
        return FlowGraphData(nodes=nodes, edges=edges)

    @classmethod
    def _normalize_code_graph(cls, graph: CodeGraphData) -> CodeGraphData:
        nodes, seen = [], set()
        for node in graph.nodes[:18]:
            if node.id in seen:
                continue
            seen.add(node.id)
            node.label = cls._clean_label(node.label or node.id.split("/")[-1], 24)
            node.description = cls._clean_label(node.description, 60) if node.description else ""
            nodes.append(node)
        edges = [edge for edge in graph.edges if edge.source in seen and edge.target in seen][:28]
        return CodeGraphData(nodes=nodes, edges=edges)

    @classmethod
    def _build_mermaid(cls, graph: FlowGraphData) -> str:
        """从结构化数据生成 Mermaid，避免让模型直接输出不稳定语法。"""
        id_map = {node.id: f"n{index}" for index, node in enumerate(graph.nodes)}
        lines = ["flowchart TD"]
        for node in graph.nodes:
            lines.append(f'    {id_map[node.id]}["{cls._clean_label(node.label, 18)}"]')
            lines.append(f"    class {id_map[node.id]} {node.type}")
        for edge in graph.edges:
            source, target = id_map[edge.source], id_map[edge.target]
            label = cls._clean_label(edge.label, 12) if edge.label else ""
            lines.append(f"    {source} -->|{label}| {target}" if label else f"    {source} --> {target}")
        lines.extend([
            "    classDef input fill:#E0F2FE,stroke:#0284C7,color:#0C4A6E",
            "    classDef process fill:#EEF2FF,stroke:#4F46E5,color:#312E81",
            "    classDef storage fill:#ECFDF5,stroke:#059669,color:#064E3B",
            "    classDef output fill:#FFF7ED,stroke:#EA580C,color:#7C2D12",
            "    classDef external fill:#F8FAFC,stroke:#64748B,color:#334155"
        ])
        return "\n".join(lines)

    @classmethod
    def _build_markdown(cls, result: FlowAnalysisResponse) -> str:
        parts = ["## 数据流概览", "", result.overview, "", "## 核心数据流图", "",
                 "```mermaid", cls._build_mermaid(result.flowchart_data), "```", "",
                 "## 关键阶段", ""]
        for index, stage in enumerate(result.stages[:8], 1):
            parts.extend([f"### {index}. {stage.title}", "", stage.description])
            if stage.input:
                parts.append(f"- 输入：{stage.input}")
            if stage.output:
                parts.append(f"- 输出：{stage.output}")
            parts.append("")
        if result.observations:
            parts.extend(["## 观察与边界", ""])
            parts.extend(f"- {item}" for item in result.observations[:6])
        return "\n".join(parts)

    def _complete_json(self, system_prompt: str, user_content: str, response_model):
        return self.llm_client.request_validated_json(
            system_prompt=system_prompt,
            user_content=user_content,
            response_model=response_model,
            temperature=0.1
        )

    def analyze_data_flow_and_graph(self, tree_structure: str, code_context: str):
        user_content = f"# 目录结构\n{tree_structure}\n\n# 精选代码\n{code_context}"

        flow_prompt = """
你是系统架构师。只根据代码证据分析一条最核心、端到端的业务数据流。
流程图必须简洁：5～10 个节点、单向为主、节点标签不超过 16 个汉字；不要把每个函数都画进去。
严格返回 JSON：
{
  "overview": "入口、处理、状态/外部依赖和输出的概览",
  "stages": [{"title":"阶段", "description":"代码如何处理", "input":"输入", "output":"输出"}],
  "flowchart_data": {
    "nodes": [{"id":"唯一英文ID", "label":"简短中文标签", "type":"input|process|storage|output|external"}],
    "edges": [{"source":"节点ID", "target":"节点ID", "label":"简短动作"}]
  },
  "observations": ["异常路径、状态边界或代码中无法确认的部分"]
}
不要返回 Mermaid、Markdown 或额外字段。
""".strip()
        flow = self._complete_json(flow_prompt, user_content, FlowAnalysisResponse)
        flow.flowchart_data = self._normalize_flow(flow.flowchart_data)

        graph_prompt = """
你是静态代码分析专家。抽取 8～18 个最核心的文件、类、函数以及真实关系。
只返回 JSON：
{
  "nodes": [{"id":"必须唯一且与边完全一致", "type":"file|class|function", "label":"短名称", "description":"职责"}],
  "edges": [{"source":"节点id", "target":"节点id", "relation":"imports|calls|defines"}]
}
禁止创建边未引用的虚构节点，禁止输出 Markdown。
""".strip()
        graph = self._complete_json(graph_prompt, user_content, CodeGraphData)
        graph = self._normalize_code_graph(graph)

        return {
            "markdown_report": self._build_markdown(flow),
            "flowchart_data": flow.flowchart_data.model_dump(),
            "graph_data": graph.model_dump()
        }
