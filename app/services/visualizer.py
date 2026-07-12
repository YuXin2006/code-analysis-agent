# app/services/visualizer.py
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any

class VisualizerService:
    def __init__(self, template_dir: str = "app/templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_name = "report.html"

    def generate_html_report(self, summary_data: Dict[str, Any], flow_graph_data: Dict[str, Any], output_path: str):
        """
        直接将原始大模型返回的 markdown 字符串与图谱数据扔给模板
        """
        template = self.env.get_template(self.template_name)
        
        # 提取大模型返回的原始 markdown 报告
        raw_markdown = flow_graph_data.get("markdown_report", "")
        
        rendered_html = template.render(
            summary=summary_data,
            raw_markdown=raw_markdown,  # 👈 保持纯净的 Markdown 文本传给前端
            graph_data=flow_graph_data["graph_data"]
        )
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
            
        print(f"🎉 可视化 HTML 报告已更新生成: {output_path}")