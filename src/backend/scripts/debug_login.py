
#!/usr/bin/env python3
"""调试登录函数的脚本"""

import sys
sys.path.append(".")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 测试缺少标识符的情况
print("=== 测试缺少标识符的情况 ===")
login_data = {
    "password": "somepassword123"
}

response = client.post(
    "/api/v1/auth/login",
    json=login_data
)

print(f"响应状态码: {response.status_code}")
print(f"响应内容: {response.text}")
if response.status_code == 200:
    print(f"响应数据: {response.json()}")
