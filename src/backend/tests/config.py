"""
测试配置文件
"""
import os
import tempfile

# 测试数据库配置 - 使用内存 SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"

# 测试数据目录
TEST_DATA_DIR = tempfile.mkdtemp()

# 测试用户配置
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
}

# 测试管理员配置
TEST_ADMIN = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "full_name": "Admin User",
    "is_admin": True
}
