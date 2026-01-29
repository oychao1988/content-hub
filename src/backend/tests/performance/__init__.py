"""
ContentHub 性能测试模块

本模块包含：
- API 响应时间测试
- 数据库查询性能测试
- 并发压力测试（使用 Locust）
- 性能基准测试（使用 pytest-benchmark）

使用方法：
1. 确保 API 服务器正在运行
2. 安装性能测试工具：pip install locust pytest-benchmark
3. 运行测试：pytest tests/performance/ -v --benchmark-only

详细文档：tests/performance/README.md
"""
