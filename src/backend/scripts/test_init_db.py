#!/usr/bin/env python3
"""测试 init_db 函数的脚本"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
settings.DATABASE_URL = "sqlite:///:memory:"

from app.db.sql_db import init_db, get_engine, Base

print("初始化数据库...")
init_db()

engine = get_engine()

# 检查是否有表创建
from sqlalchemy import inspect
inspector = inspect(engine)
print("数据库中的表:", inspector.get_table_names())