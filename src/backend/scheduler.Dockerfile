# ContentHub 调度器专用容器 Dockerfile
# 基于后端镜像，仅运行调度器服务

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制应用代码
COPY . .

# 复制并设置脚本权限
COPY scripts/init_scheduler.py /app/scripts/init_scheduler.py
COPY scripts/scheduler_entrypoint.sh /app/scripts/scheduler_entrypoint.sh
RUN chmod +x /app/scripts/init_scheduler.py && \
    chmod +x /app/scripts/scheduler_entrypoint.sh

# 创建数据目录并设置权限
RUN mkdir -p /app/data /app/logs /app/scripts && \
    chmod -R 755 /app/data /app/logs /app/scripts

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "from app.services.scheduler_service import scheduler_service; exit(0 if scheduler_service.is_running else 1)"

# 使用调度器专用入口脚本
CMD ["/app/scripts/scheduler_entrypoint.sh"]
