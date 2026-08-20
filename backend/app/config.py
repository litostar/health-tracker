"""
全局配置：从环境变量 / .env 读取。
使用 python-dotenv 在本地开发时加载 .env 文件。
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 单用户访问口令：前端和 iPhone 快捷指令都需在 Header 带 Bearer <API_TOKEN>
API_TOKEN = os.getenv("API_TOKEN", "change_me_to_a_strong_token")

# SQLite 数据库地址
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./health.db")

# CORS 允许的源（逗号分隔，支持多个）
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# 服务端口（云平台通常用环境变量 PORT）
PORT = int(os.getenv("PORT", "8000"))
