"""
数据库层：基于 SQLAlchemy 操作 SQLite。
SQLite 是文件型数据库，零配置、适合个人项目；生产环境把文件放到持久磁盘即可。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

# connect_args 里的 check_same_thread=False 是 FastAPI 在多线程下访问 SQLite 的必选项
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# 每个请求一个会话，用完关闭（见 get_db）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有模型继承这个 Base
Base = declarative_base()


def get_db():
    """FastAPI 依赖：请求级数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """首次运行时建表。导入 models 确保表已注册到 Base.metadata"""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
