#!/usr/bin/env python3
"""
调试脚本 - 检查FastAPI实际注册的路由
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.factory import create_app
from app.core.config import settings

print("=== 创建应用实例 ===")
app = create_app()

print("\n=== 已注册的API路由 ===")
for route in app.routes:
    if hasattr(route, "path") and route.path.startswith("/api/v1"):
        print(f"{route.methods} {route.path}")

print("\n=== platforms路由详细信息 ===")
for route in app.routes:
    if hasattr(route, "path") and "/platforms" in route.path:
        print(f"\n路由: {route.methods} {route.path}")
        if hasattr(route, "endpoint"):
            import inspect
            sig = inspect.signature(route.endpoint)
            print(f"参数: {list(sig.parameters.keys())}")