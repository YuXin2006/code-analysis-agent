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
    
    model_config = SettingsConfigDict(env_file=os.path.join(BASE_DIR, ".env"), env_file_encoding="utf-8")

settings = Settings()