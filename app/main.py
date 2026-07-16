# app/main.py
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.services.tech_detector import TechDetectorService
from app.services.data_flow import DataFlowService
from app.services.code_parser import CodeParserService
from app.utils.file_utils import generate_tree_structure
from app.core.config import settings
import os
import shutil
import uuid
from pathlib import Path

app = FastAPI(title="代码分析助手", description="拖拽文件夹上传，自动生成技术分析报告")

# 创建必要的目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp")
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回前端页面"""
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="前端页面未找到，请先创建 static/index.html")

@app.post("/api/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    rel_paths: list[str] = Form(default=[]),
    session_id: str | None = Form(default=None)
):
    """接收上传的文件，保存到临时目录"""
    # 如果没有提供 session_id，则生成新的
    if not session_id:
        session_id = str(uuid.uuid4())
    else:
        try:
            session_id = str(uuid.UUID(session_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="session_id 不合法") from exc
    
    project_dir = Path(TEMP_DIR, session_id).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    
    for index, file in enumerate(files):
        if file.size is not None and file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"文件 {file.filename} 超过 {settings.MAX_FILE_SIZE_MB} MB 限制"
            )
        relative_dir = rel_paths[index] if index < len(rel_paths) else ""
        relative_dir = relative_dir.replace("\\", "/").strip("/")
        file_path = (project_dir / relative_dir / Path(file.filename).name).resolve()
        if project_dir not in file_path.parents:
            raise HTTPException(status_code=400, detail="上传路径不合法")
        
        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        with file_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    
    return {"session_id": session_id, "message": f"成功上传 {len(files)} 个文件"}

@app.post("/api/analyze/{session_id}")
async def analyze_project(session_id: str, analysis_type: str = "summary"):
    """分析项目代码"""
    project_dir = os.path.join(TEMP_DIR, session_id)
    
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        if analysis_type == "summary":
            # 技术栈分析
            detector = TechDetectorService()
            result = detector.execute_analysis(project_dir)
            return {
                "type": "summary",
                "background": result.background,
                "architecture_summary": result.architecture_summary,
                "core_features": result.core_features,
                "entry_points": result.entry_points,
                "directory_modules": [item.model_dump() for item in result.directory_modules],
                "data_and_config": result.data_and_config,
                "risks_and_notes": result.risks_and_notes,
                "tech_stack": {
                    "language": result.tech_stack.language,
                    "framework": result.tech_stack.framework,
                    "database": result.tech_stack.database or "",
                    "tools": result.tech_stack.tools,
                    "frontend": result.tech_stack.frontend,
                    "backend": result.tech_stack.backend,
                    "data_storage": result.tech_stack.data_storage,
                    "testing": result.tech_stack.testing,
                    "deployment": result.tech_stack.deployment,
                    "evidence": [item.model_dump() for item in result.tech_stack.evidence]
                },
                "directory_tree": generate_tree_structure(project_dir)
            }
        elif analysis_type == "flow":
            # 数据流分析
            tree_str = generate_tree_structure(project_dir)
            code_ctx = CodeParserService.prepare_llm_context(project_dir)
            flow_service = DataFlowService()
            result = flow_service.analyze_data_flow_and_graph(tree_str, code_ctx)
            return {
                "type": "flow",
                "markdown_report": result["markdown_report"],
                "flowchart_data": result["flowchart_data"],
                "graph_data": result["graph_data"]
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的分析类型")
    finally:
        # 清理临时文件
        shutil.rmtree(project_dir, ignore_errors=True)

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
