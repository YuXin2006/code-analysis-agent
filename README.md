# code-analysis-agent
This is an intelligent agent that, when given some code documents, can help you deeply analyze the code and generate beautiful, visual output.

# 项目结构
code-analysis-agent/
├── app/
│   ├── main.py
│   ├── core/                  #  【新增】核心配置与中间件
│   │   ├── config.py          # 环境变量与 LLM API Key 配置
│   │   └── security.py        # API 密钥或跨域配置
│   ├── routers/
│   │   └── analyzer.py
│   ├── services/
│   │   ├── code_parser.py
│   │   ├── tech_detector.py
│   │   ├── data_flow.py
│   │   ├── visualizer.py
│   │   └── llm_client.py     #  【新增】封装与大模型的交互逻辑（如LangChain 封装）
│   ├── schemas/               #  【新增】Pydantic 响应与请求的模型定义
│   │   ├── analysis.py        # 定义输入输出的 JSON 结构
│   │   └── graph.py           # 定义知识图谱/Mermaid 的数据结构
│   ├── templates/
│   │   └── report.html
│   └── utils/
│       └── file_utils.py
├── data/                      #  【新增】本地临时缓存或图数据序列化存储
│   ├── uploads/               # 存放用户上传并解压的代码压缩包
│   └── cache/                 # 存放解析完的图数据或 AST 缓存
├── tests/
├── requirements.txt
└── README.md
# 技术栈选型
1. 后端核心（FastAPI 框架）
基础框架： FastAPI + Uvicorn（高性能、原生异步、自带 Swagger 文档）。

配置与校验： pydantic-settings（管理环境变量和 .env）。

异步任务： FastAPI 自带的 BackgroundTasks（用于 MVP 阶段异步分析，防止 HTTP 超时）。

2. AI 与 Agent 推理（大模型层）
Agent 框架： LangChain 或 LangGraph。对于多步骤、有状态的代码分析（如先抓结构，再填细节），LangGraph 的状态机机制最为精准。

核心 LLM： Claude 3.5 Sonnet 或 DeepSeek-Coder-V2（代码逻辑理解、结构化 JSON 输出和 Mermaid 脚本生成能力在当前梯队中最强）。

AST 解析（本地辅助）： tree-sitter 或 Python 内置的 ast 模块。用本地脚本静态解析出基础的类、函数关系，能帮 LLM 大幅节省 Token 并提升准确率。

3. 前端与美化展示（报告层）
静态报告（后端生成）： Jinja2 模板引擎（用于将分析结果动态渲染进 report.html）。

图表与流程图： Mermaid.js（直接将 LLM 生成的文本渲染成时序图、架构图）。

知识图谱交互： AntV G6 或 ECharts (Graph)（通过 JSON 数据源渲染可拖拽、点击的核心代码调用图谱）。

# 功能模块拆解和核心功能
1. 文件夹预处理（file_utils.py & code_parser.py）
任务： 接收上传的 .zip 压缩包，解压到 data/uploads/，遍历文件。
过滤黑名单：剔除 .git, node_modules, venv, dist, __pycache__ 等。
目录树生成：构建一个树状的 JSON 对象（如 {"name": "root", "children": [...]}）。
代码提取：读取所有合规的文本文件（.py, .js, .ts, .go, .java 等），记录文件名、相对路径和文件内容。

2. 技术栈深度检测（tech_detector.py）
任务： 识别项目用了什么语言、什么框架、哪些数据库和核心依赖。
静态扫描： 优先读取包管理文件（package.json, requirements.txt, go.mod）。
LLM 研判： 如果依赖文件不全，将依赖列表或核心入口代码发给 LLM，让其通过 Pydantic 结构化输出（Structured Output）返回一个标准 JSON。
输出示例： {"language": "Python", "framework": "Django", "database": "MySQL", "tools": ["Redis", "Docker"]}
3. 数据流与业务功能分析（data_flow.py）
任务： 梳理项目的核心业务、用户请求是如何流转的、数据是如何进出数据库的。
全局背景扫描： 让 LLM 快速通读 README.md 和主要入口文件，总结项目背景。
接口与模型关联： 让 LLM 专门分析路由文件（如 FastAPI 的 routers）和数据库模型文件（如 ORM models）。
生成 Mermaid 脚本： 指导 LLM 将流转逻辑转化为 Mermaid 的 graph TD 语法。

4. 知识图谱数据生成（llm_client.py & visualizer.py）
任务： 提取代码中的高价值实体（文件、类、函数）及其关联，为前端图谱准备数据。
编写 Strict Prompt，要求 LLM 分析代码模块后，严格返回符合 schemas/graph.py 定义的结构：

JSON
{
  "nodes": [{"id": "main.py", "type": "file"}, {"id": "analyze_code", "type": "function"}],
  "edges": [{"source": "main.py", "target": "analyze_code", "relation": "defines"}]
}
visualizer.py 收集所有的文本总结、Mermaid 脚本和图谱 JSON，将其注入到 HTML 模板中。
5. API 路由与控制器（analyzer.py）
任务： 暴露给前端的接口，串联上述所有流程。
示例:
POST /api/v1/analyzer/upload：接收文件，触发后台任务 BackgroundTasks，立即返回 {"task_id": "xxx", "status": "processing"}。

GET /api/v1/analyzer/task/{task_id}：前端轮询该接口。当状态为 completed 时，返回美化后的数据或 HTML 报告的下载链接。