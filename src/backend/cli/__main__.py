"""
CLI 入口点

配置日志级别以减少不必要的输出。
"""
import sys
import os
import logging

# 在导入任何模块之前，禁用所有logging输出
logging.disable(logging.CRITICAL)

# 设置环境变量，控制loguru日志输出
os.environ['LOG_LEVEL'] = 'ERROR'
os.environ['LOG_FILE'] = 'false'

# 导入主应用
from cli.main import app

if __name__ == "__main__":
    app()
