# 更新日志

## [未发布] - 2026-02-08

### 修复 (Fixed)
- **修复依赖缺失导致所有业务模块无法加载的问题**
  - 添加 `pydantic[email]==2.5.3` 到 requirements.txt
  - 添加 `redis>=5.0.0` 到 requirements.txt
  - 修复前：0/12 模块加载成功（0%）
  - 修复后：13/13 模块加载成功（100%）

- **修复 Docker Compose 命令兼容性问题**
  - Makefile 中所有 `docker compose` 命令改为 `docker-compose`
  - 解决 `unknown shorthand flag: 'd' in -d` 错误

- **删除过时的 Docker Compose 版本字段**
  - docker-compose.yml：删除 `version: '3.8'`
  - 消除 "the attribute 'version' is obsolete" 警告

- **统一容器内外端口配置**
  - src/backend/Dockerfile：后端端口统一使用 18010
  - 修复健康检查和 gunicorn 绑定地址

- **升级前端 Node.js 版本**
  - src/frontend/Dockerfile：Node.js 从 v18 升级到 v20-alpine
  - 修复 Vite 7.3.1 兼容性问题（crypto.hash 错误）

### 改进 (Improved)
- 完善容器健康检查机制
- 优化 Docker 镜像构建流程

### 技术细节
- **构建时间**：约 50 分钟（受网络速度影响，主要是下载 gcc/g++ 71.4MB）
- **镜像大小**：后端镜像包含完整 Python 依赖
- **依赖包数量**：安装 80+ 个 Python 包

### 验证结果
- ✅ 所有容器健康检查通过
- ✅ 前端界面可访问（http://localhost:18030）
- ✅ 后端 API 可访问（http://localhost:18010）
- ✅ API 文档可访问（http://localhost:18010/docs）
- ✅ 数据库初始化成功（17 个表）
- ✅ 审计日志正常工作
