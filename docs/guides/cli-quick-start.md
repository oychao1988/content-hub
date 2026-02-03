# ContentHub CLI 快速开始指南

> **版本**: 1.0.0
> **更新日期**: 2026-02-04
> **适用对象**: 运维人员、开发人员、系统管理员

---

## 目录

- [安装说明](#安装说明)
- [首次使用流程](#首次使用流程)
- [常用场景](#常用场景)
- [故障排除](#故障排除)
- [相关文档](#相关文档)

---

## 安装说明

### 方式一：使用安装脚本（推荐）

```bash
# 1. 进入项目目录
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 2. 安装 CLI 到系统路径
sudo bash scripts/install-cli.sh

# 3. 验证安装
contenthub --version
```

安装后可以在任何目录使用 `contenthub` 命令。

### 方式二：直接使用 Python 模块

```bash
# 进入后端目录
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 使用 Python 模块方式运行
python -m cli.main --help
```

### 依赖要求

- Python 3.8+
- 所有依赖已在 `requirements.txt` 中列出

```bash
pip install -r requirements.txt
```

---

## 首次使用流程

### 步骤 1: 初始化数据库

```bash
# 方式一：创建全新数据库（推荐用于测试）
contenthub db init

# 方式二：从已有数据库初始化（生产环境）
contenthub db migrate
```

**输出示例**:
```
✓ 数据库初始化成功
✓ 创建了 15 张表
✓ 数据库文件: data/contenthub.db
```

### 步骤 2: 创建管理员用户

```bash
contenthub users create \
  --username admin \
  --email admin@example.com \
  --password admin123 \
  --role admin
```

**参数说明**:
- `--username`: 用户名（必填）
- `--email`: 邮箱地址（必填）
- `--password`: 密码（可选，不指定则自动生成）
- `--role`: 角色（admin/editor/operator，默认为 operator）

**输出示例**:
```
✓ 用户创建成功
  用户ID: 1
  用户名: admin
  邮箱: admin@example.com
  角色: admin
  状态: active
```

### 步骤 3: 验证系统状态

```bash
# 检查系统健康状态
contenthub system health

# 查看数据库统计
contenthub db stats

# 查看用户列表
contenthub users list
```

---

## 常用场景

### 场景 1: 初始化新系统

完整的系统初始化流程：

```bash
# 1. 初始化数据库
contenthub db init

# 2. 创建管理员
contenthub users create --username admin --email admin@example.com --role admin

# 3. 创建编辑用户
contenthub users create --username editor --email editor@example.com --role editor

# 4. 创建运营人员
contenthub users create --username operator --email operator@example.com --role operator

# 5. 验证系统
contenthub system health
```

### 场景 2: 创建平台和客户

```bash
# 1. 创建微信公众号平台
contenthub platform create \
  --name "微信公众号" \
  --code weixin \
  --type weixin \
  --api-url "https://api.weixin.qq.com" \
  --api-key "your_api_key"

# 2. 创建客户
contenthub customer create \
  --name "示例客户" \
  --contact-name "张三" \
  --contact-email "zhangsan@example.com" \
  --contact-phone "13800138000" \
  --description "示例客户描述"

# 3. 查看列表
contenthub platform list
contenthub customer list
```

### 场景 3: 创建和管理账号

```bash
# 1. 创建账号（绑定平台和客户）
contenthub accounts create \
  --name "测试公众号" \
  --platform-id 1 \
  --customer-id 1 \
  --app-id "wx1234567890" \
  --app-secret "your_app_secret"

# 2. 查看账号详情
contenthub accounts show --id 1

# 3. 测试账号连接
contenthub accounts test --id 1

# 4. 启用/禁用账号
contenthub accounts update --id 1 --is-active true
```

### 场景 4: 内容生成和发布

```bash
# 1. 生成内容
contenthub content generate \
  --title "如何使用 ContentHub" \
  --keywords "ContentHub,教程,快速开始" \
  --style "professional"

# 2. 查看生成的内容
contenthub content list --status generated

# 3. 提交审核
contenthub content review --id 1 --action approve --comment "内容良好"

# 4. 发布内容
contenthub publisher publish \
  --content-id 1 \
  --account-id 1

# 5. 查看发布状态
contenthub publisher status --id 1
```

### 场景 5: 定时任务管理

```bash
# 1. 创建定时生成任务
contenthub scheduler create \
  --name "每日内容生成" \
  --type content_generation \
  --cron "0 9 * * *" \
  --params '{"keywords": ["AI", "技术"], "count": 5}'

# 2. 启动调度器
contenthub scheduler start

# 3. 查看任务列表
contenthub scheduler list

# 4. 查看任务执行历史
contenthub scheduler history --job-id 1

# 5. 暂停任务
contenthub scheduler pause --id 1

# 6. 恢复任务
contenthub scheduler resume --id 1
```

### 场景 6: 系统维护

```bash
# 1. 数据库备份
contenthub db backup --output backups/db_backup_$(date +%Y%m%d).db

# 2. 查看系统统计
contenthub dashboard stats

# 3. 查看审计日志
contenthub audit list --limit 50

# 4. 清理过期数据
contenthub db cleanup --days 30

# 5. 检查系统健康
contenthub system health
```

### 场景 7: 配置管理

```bash
# 1. 查看当前配置
contenthub config list

# 2. 获取特定配置
contenthub config get --key content.default_style

# 3. 设置配置
contenthub config set --key content.default_style --value "professional"

# 4. 重置为默认值
contenthub config reset --key content.default_style

# 5. 验证配置
contenthub config validate
```

---

## 全局选项

所有命令都支持以下全局选项：

```bash
contenthub <module> <command> [OPTIONS]

# 常用全局选项
--format <format>    # 输出格式: table（默认）、json、csv
--debug              # 启用调试模式（显示详细日志）
--quiet              # 静默模式（仅输出错误）
--user <username>    # 指定操作用户（用于审计）
```

**示例**:

```bash
# JSON 格式输出
contenthub users list --format json

# 调试模式
contenthub content generate --debug

# 指定操作用户
contenthub accounts create --user admin --name "测试账号"
```

---

## 故障排除

### 问题 1: 数据库锁定

**症状**: 执行命令时提示 "database is locked"

**解决方案**:

```bash
# 1. 检查是否有其他进程在使用数据库
ps aux | grep contenthub

# 2. 停止 Web 服务器（如果正在运行）
# Ctrl+C 或 kill <pid>

# 3. 尝试重新执行命令
contenthub db stats
```

### 问题 2: 权限不足

**症状**: 提示 "Permission denied" 或无法写入文件

**解决方案**:

```bash
# 1. 检查数据目录权限
ls -la data/

# 2. 修改权限
chmod 755 data/
chmod 644 data/*.db

# 3. 如果使用 SQLite，确保数据库文件可写
touch data/contenthub.db
chmod 664 data/contenthub.db
```

### 问题 3: 模块导入错误

**症状**: 提示 "ModuleNotFoundError" 或 "ImportError"

**解决方案**:

```bash
# 1. 检查 Python 路径
cd src/backend
python -c "import sys; print('\n'.join(sys.path))"

# 2. 重新安装依赖
pip install -r requirements.txt --upgrade

# 3. 检查环境变量
echo $PYTHONPATH

# 4. 如果需要，设置 PYTHONPATH
export PYTHONPATH=/Users/Oychao/Documents/Projects/content-hub/src/backend:$PYTHONPATH
```

### 问题 4: 命令找不到

**症状**: 提示 "command not found: contenthub"

**解决方案**:

```bash
# 方式一：使用完整路径
cd /Users/Oychao/Documents/Projects/content-hub/src/backend
python -m cli.main <command>

# 方式二：重新安装 CLI
sudo bash scripts/install-cli.sh

# 方式三：创建别名
alias contenthub='cd /Users/Oychao/Documents/Projects/content-hub/src/backend && python -m cli.main'
# 添加到 ~/.bashrc 或 ~/.zshrc
```

### 问题 5: API 连接失败

**症状**: 提示 "Connection refused" 或 "API Error"

**解决方案**:

```bash
# 1. 检查配置文件
cat .env | grep API

# 2. 测试网络连接
curl -I https://api.weixin.qq.com

# 3. 检查 API 密钥
contenthub config get --key publisher.api_key

# 4. 更新配置
contenthub config set --key publisher.api_url --value "https://api.example.com"
```

### 问题 6: 定时任务不执行

**症状**: 创建的定时任务没有按预期执行

**解决方案**:

```bash
# 1. 检查调度器状态
contenthub scheduler status

# 2. 启动调度器
contenthub scheduler start

# 3. 查看任务状态
contenthub scheduler list

# 4. 检查任务配置
contenthub scheduler show --id 1

# 5. 查看执行日志
contenthub scheduler history --job-id 1 --limit 10

# 6. 验证 cron 表达式
# 可以使用在线工具验证: https://crontab.guru/
```

---

## 性能优化建议

### 大批量操作

```bash
# 1. 批量生成内容时使用循环
for i in {1..10}; do
  contenthub content generate \
    --title "文章 $i" \
    --keywords "测试" \
    --quiet
done

# 2. 使用 JSON 格式输出便于脚本处理
contenthub users list --format json > users.json

# 3. 使用 --quiet 模式减少输出
contenthub db cleanup --quiet
```

### 日志管理

```bash
# 1. 查看日志文件
tail -f logs/contenthub.log

# 2. 查看错误日志
tail -f logs/error_$(date +%Y-%m-%d).log

# 3. 清理旧日志
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 相关文档

### 详细参考

- **完整命令参考**: [CLI-REFERENCE.md](../references/CLI-REFERENCE.md)
- **架构设计**: [../architecture/CLI-ARCHITECTURE.md](../architecture/CLI-ARCHITECTURE.md)
- **系统设计**: [../design/cli-system-design.md](../design/cli-system-design.md)

### 使用指南

- **数据库管理**: [../guides/database-management.md](../guides/database-management.md)
- **内容管理**: [../guides/content-management.md](../guides/content-management.md)
- **定时任务**: [../guides/scheduler-guide.md](../guides/scheduler-guide.md)

### API 文档

- **FastAPI 文档**: http://localhost:8000/docs
- **发布器 API**: [../references/publisher-api.md](../references/publisher-api.md)

---

## 获取帮助

### 内置帮助

```bash
# 查看所有命令
contenthub --help

# 查看模块帮助
contenthub users --help

# 查看命令帮助
contenthub users create --help
```

### 在线资源

- **GitHub Issues**: https://github.com/your-org/content-hub/issues
- **文档站点**: https://docs.contenthub.example.com
- **社区论坛**: https://community.contenthub.example.com

---

## 下一步

1. 阅读 [CLI-REFERENCE.md](../references/CLI-REFERENCE.md) 了解所有命令详情
2. 查看 [使用案例](../use-cases/) 了解实际应用场景
3. 配置定时任务实现自动化运营
4. 集成到 CI/CD 流程中

---

**提示**: 建议收藏本文档，方便日常查阅。如需更多帮助，请查看相关文档或联系技术支持。
