import os
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.utils.custom_logger import log

_engine = None
_session_local: Optional[sessionmaker] = None

# 创建基类
Base = declarative_base()


def _ensure_sqlite_dir(db_url: str) -> dict:
    """
    如果是 sqlite，确保父目录存在并设置必要的连接参数。
    """
    connect_args = {}
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "", 1)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        connect_args = {"check_same_thread": False}
    return connect_args


def get_engine():
    global _engine
    if _engine is not None:
        return _engine
    
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    connect_args = _ensure_sqlite_dir(settings.DATABASE_URL)
    _engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.LOG_SQL_QUERIES and settings.DEBUG,
        connect_args=connect_args,
    )

    if settings.LOG_SQL_QUERIES:

        @event.listens_for(_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault("query_start_time", []).append(time.time())
            if not executemany:
                log.debug(f"SQL Query: {statement}")
                log.debug(f"Parameters: {parameters}")

        @event.listens_for(_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info["query_start_time"].pop(-1)
            if not executemany:
                log.debug(f"Query Complete Time: {total:.3f}s")

    return _engine


def get_session_local() -> sessionmaker:
    global _session_local
    if _session_local is not None:
        return _session_local

    engine = get_engine()
    _session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _session_local


def init_db() -> None:
    """
    初始化数据库
    """
    try:
        # 创建所有表
        engine = get_engine()
        # 导入所有模型以注册到 Base.metadata
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        log.info("数据库初始化成功")
    except Exception as e:
        log.error(f"数据库初始化失败: {e}")
        raise


@contextmanager
def DBContext() -> Generator[Session, None, None]:
    """
    数据库会话上下文管理器
    """
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


# 依赖注入函数
def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    """
    with DBContext() as db:
        yield db




