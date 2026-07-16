# app/core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取项目根目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings(BaseSettings):
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-v4-pro"
    MAX_FILE_SIZE_MB: int = 10
    # 控制发给模型的上下文规模，避免大型仓库直接超出模型窗口。
    MAX_CONTEXT_CHARS: int = 180_000
    MAX_CONTEXT_FILES: int = 160
    MAX_CHARS_PER_FILE: int = 18_000
    TREE_MAX_DEPTH: int = 8
    TREE_MAX_ENTRIES: int = 2_000
    LLM_JSON_MAX_ATTEMPTS: int = 3
    LLM_MAX_OUTPUT_TOKENS: int = 8192
    
    model_config = SettingsConfigDict(env_file=os.path.join(BASE_DIR, ".env"), env_file_encoding="utf-8")

settings = Settings()
