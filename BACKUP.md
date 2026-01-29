# ContentHub 备份使用指南

本文档详细说明 ContentHub 系统的备份策略、使用方法和恢复流程。

## 目录

- [备份策略](#备份策略)
- [快速开始](#快速开始)
- [数据库备份](#数据库备份)
- [文件备份](#文件备份)
- [定时备份配置](#定时备份配置)
- [备份验证](#备份验证)
- [恢复流程](#恢复流程)
- [备份文件管理](#备份文件管理)
- [常见问题排查](#常见问题排查)
- [最佳实践](#最佳实践)

---

## 备份策略

### 备份类型

ContentHub 提供两种备份类型：

1. **全量备份（Full Backup）**
   - 完整备份整个数据库或文件系统
   - 文件大小较大，但恢复时只需一个文件
   - 建议频率：每天一次

2. **增量备份（Incremental Backup）**
   - 仅备份自上次备份以来的变化
   - 文件较小，节省空间和时间
   - 建议频率：每 4 小时一次

### 默认备份计划

```
数据库全量备份:   每天凌晨 2:00
数据库增量备份:   每 4 小时 (6:00, 10:00, 14:00, 18:00, 22:00)
文件备份:         每天凌晨 3:00
旧备份清理:       每周日凌晨 4:00
```

### 备份保留策略

- 所有备份保留 30 天
- 30 天前的备份自动归档到 `old/` 目录
- 失败的备份移动到 `failed/` 目录

---

## 快速开始

### 1. 首次备份

```bash
# 进入后端目录
cd src/backend

# 创建必要的目录
mkdir -p backups/db backups/files logs

# 执行数据库全量备份
./scripts/backup_db.sh --type full

# 执行文件备份
./scripts/backup_files.sh --full
```

### 2. 安装定时备份

```bash
# 安装所有定时任务（推荐）
./scripts/cron_backup_setup.sh --install

# 查看已安装的定时任务
./scripts/cron_backup_setup.sh --list

# 查看备份服务状态
./scripts/cron_backup_setup.sh --status
```

### 3. 验证备份

```bash
# 验证所有数据库备份
./scripts/verify_backup.sh --all --type db

# 验证所有文件备份
./scripts/verify_backup.sh --all --type files

# 生成验证报告
./scripts/verify_backup.sh --all --type db --report reports/verify_report.json
```

---

## 数据库备份

### 备份脚本

`scripts/backup_db.sh` 提供 SQLite 数据库的完整备份功能。

### 功能特性

- SQLite 在线备份（使用 `.backup` 命令）
- 数据库完整性验证
- MD5 校验和生成
- Gzip 压缩
- 自动清理旧备份

### 使用方法

#### 全量备份

```bash
./scripts/backup_db.sh --type full
```

**输出示例**:
```
[2026-01-29 14:30:00] [INFO] [DB] 开始全量备份...
正在执行全量备份...
[2026-01-29 14:30:00] [INFO] [DB] 磁盘空间检查通过，可用: 51200MB
[2026-01-29 14:30:01] [INFO] [DB] 数据库复制成功
[2026-01-29 14:30:02] [INFO] [DB] 压缩成功
[2026-01-29 14:30:02] [INFO] [DB] 全量备份完成: backups/db/contenthub_20260129_143000.db.gz
✓ 全量备份完成: contenthub_20260129_143000.db.gz
```

#### 增量备份

```bash
./scripts/backup_db.sh --type incremental
```

**注意**: SQLite 的增量备份实际上是完整备份，但使用 `VACUUM INTO` 创建一个干净的副本，并标记为增量。

#### 列出备份

```bash
./scripts/backup_db.sh --list
```

**输出示例**:
```
=== 数据库备份列表 ===

备份目录: /path/to/backups/db

备份文件                                    备份时间              大小
----------------------------------------  ---------------  ----------
contenthub_20260129_020000.db.gz          2026-01-29 02:00  1.2M
contenthub_20260129_060000.db.gz          2026-01-29 06:00  1.1M
contenthub_20260129_100000.db.gz          2026-01-29 10:00  1.1M

总计大小: 3.4M
```

#### 清理旧备份

```bash
./scripts/backup_db.sh --clean
```

**输出示例**:
```
[2026-01-29 14:35:00] [INFO] [DB] 清理超过 30 天的旧备份...
正在清理旧备份...
[2026-01-29 14:35:01] [INFO] [DB] 已归档旧备份: contenthub_20251230_020000.db.gz
✓ 清理完成，归档了 5 个备份文件，释放空间: 15MB
```

### 备份文件结构

```
backups/db/
├── contenthub_20260129_020000.db.gz           # 全量备份
├── contenthub_20260129_020000.db.gz.md5       # MD5 校验和
├── contenthub_20260129_060000.db.gz           # 增量备份
├── contenthub_20260129_060000.db.gz.md5
├── old/                                       # 旧备份归档
│   └── contenthub_20251230_020000.db.gz
└── failed/                                    # 失败的备份
```

---

## 文件备份

### 备份脚本

`scripts/backup_files.sh` 提供内容文件和图片文件的备份功能。

### 默认备份目录

- `accounts/` - 账号配置文件
- `uploads/` - 上传的图片和文件

### 使用方法

#### 完整备份

```bash
# 备份所有默认目录
./scripts/backup_files.sh --full

# 备份指定目录
./scripts/backup_files.sh --source accounts/ --source uploads/ --full

# 备份到指定位置
./scripts/backup_files.sh --source uploads/ --dest /tmp/backup --full
```

**输出示例**:
```
[2026-01-29 14:40:00] [INFO] [FILES] 开始完整备份...
正在执行完整备份...
[2026-01-29 14:40:00] [INFO] [FILES] 源目录总大小: 25MB
[2026-01-29 14:40:01] [INFO] [FILES] 压缩包创建成功
[2026-01-29 14:40:02] [INFO] [FILES] 完整备份完成: backups/files/files_20260129_140000_full.tar.gz
✓ 完整备份完成: files_20260129_140000_full.tar.gz
```

#### 增量备份

```bash
# 基于最新完整备份的增量备份
./scripts/backup_files.sh --source accounts/ --incremental
```

**输出示例**:
```
[2026-01-29 14:45:00] [INFO] [FILES] 开始增量备份...
正在执行增量备份...
[2026-01-29 14:45:00] [INFO] [FILES] 基于完整备份: files_20260129_020000_full.tar.gz
[2026-01-29 14:45:01] [INFO] [FILES] 检测到 12 个文件有变化
[2026-01-29 14:45:02] [INFO] [FILES] 增量备份完成: backups/files/files_20260129_140000_incremental.tar.gz
✓ 增量备份完成: files_20260129_140000_incremental.tar.gz
```

#### 列出备份

```bash
./scripts/backup_files.sh --list
```

**输出示例**:
```
=== 文件备份列表 ===

备份目录: /path/to/backups/files

备份文件                                            备份时间              类型    大小
---------------------------------------------  ---------------  -------  ----------
files_20260129_030000_full.tar.gz             2026-01-29 03:00  完整    8.5M
files_20260129_140000_incremental.tar.gz      2026-01-29 14:00  增量    1.2M

总计大小: 9.7M
```

### 备份清单文件

每个备份文件都会生成一个 `.manifest` 清单文件：

```
备份时间: 2026-01-29 14:00:00
备份类型: 完整备份
源目录:
  - /path/to/accounts
  - /path/to/uploads
原始大小: 25MB
压缩后大小: 8.5M
压缩率: 66%
```

---

## 定时备份配置

### 配置脚本

`scripts/cron_backup_setup.sh` 用于管理定时备份任务。

### 使用方法

#### 安装定时任务

```bash
# 安装所有定时任务
./scripts/cron_backup_setup.sh --install
```

**已安装的定时任务**:
```
# ContentHub 自动备份任务

# 数据库全量备份 - 每天凌晨 2:00
0 2 * * * /path/to/backup_db.sh --type full >> /path/to/logs/backup.log 2>&1

# 数据库增量备份 - 每 4 小时
0 6,10,14,18,22 * * * /path/to/backup_db.sh --type incremental >> /path/to/logs/backup.log 2>&1

# 文件备份 - 每天凌晨 3:00
0 3 * * * /path/to/backup_files.sh --full >> /path/to/logs/backup.log 2>&1

# 清理旧备份 - 每周日凌晨 4:00
0 4 * * 0 /path/to/backup_db.sh --clean >> /path/to/logs/backup.log 2>&1
0 5 * * 0 /path/to/backup_files.sh --clean >> /path/to/logs/backup.log 2>&1
```

#### 启用特定任务

```bash
# 仅启用数据库全量备份
./scripts/cron_backup_setup.sh --enable-db-full

# 仅启用数据库增量备份
./scripts/cron_backup_setup.sh --enable-db-incremental

# 仅启用文件备份
./scripts/cron_backup_setup.sh --enable-files
```

#### 卸载定时任务

```bash
./scripts/cron_backup_setup.sh --uninstall
```

#### 查看定时任务

```bash
./scripts/cron_backup_setup.sh --list
```

#### 查看服务状态

```bash
./scripts/cron_backup_setup.sh --status
```

**输出示例**:
```
=== 备份服务状态 ===

✓ Cron 服务状态: 运行中
✓ 定时任务状态: 已安装

✓ 数据库备份: 12 个文件
✓ 文件备份: 5 个文件

最近 5 条备份日志:
  [2026-01-29 14:00:00] [INFO] [DB] 开始全量备份...
  [2026-01-29 14:00:02] [INFO] [DB] 全量备份完成
  [2026-01-29 14:05:00] [INFO] [FILES] 开始完整备份...
  [2026-01-29 14:05:02] [INFO] [FILES] 完整备份完成
  [2026-01-29 14:10:00] [INFO] [DB] 开始增量备份...

备份目录可用空间: 45GB
```

### 自定义定时计划

编辑 crontab 以自定义备份时间：

```bash
# 编辑当前用户的 crontab
crontab -e

# 查找 "ContentHub 自动备份任务"
# 修改时间规则，例如：
0 */2 * * * /path/to/backup_db.sh --type incremental  # 每 2 小时
30 3 * * * /path/to/backup_files.sh --full            # 每天凌晨 3:30
```

---

## 备份验证

### 验证脚本

`scripts/verify_backup.sh` 用于验证备份文件的完整性。

### 验证项

1. 文件存在性检查
2. 文件大小验证
3. MD5 校验和验证
4. 压缩文件完整性测试
5. 数据库完整性检查（针对数据库备份）
6. 文件恢复测试（针对文件备份）

### 使用方法

#### 验证单个备份

```bash
# 验证数据库备份
./scripts/verify_backup.sh --file backups/db/contenthub_20260129.db.gz

# 验证文件备份
./scripts/verify_backup.sh --file backups/files/files_20260129.tar.gz
```

**输出示例**:
```
验证: contenthub_20260129.db.gz
[2026-01-29 15:00:00] [INFO] 文件存在: backups/db/contenthub_20260129.db.gz
[2026-01-29 15:00:00] [INFO] 文件大小正常: backups/db/contenthub_20260129.db.gz (1228800 bytes)
[2026-01-29 15:00:01] [INFO] MD5 校验通过: backups/db/contenthub_20260129.db.gz
[2026-01-29 15:00:02] [INFO] Gzip 压缩文件完整: backups/db/contenthub_20260129.db.gz
[2026-01-29 15:00:03] [INFO] 数据库验证通过: backups/db/contenthub_20260129.db.gz
[2026-01-29 15:00:03] [INFO]   包含表: accounts, contents, schedulers, publishers, ...
✓ 验证通过
```

#### 验证所有备份

```bash
# 验证所有数据库备份
./scripts/verify_backup.sh --all --type db

# 验证所有文件备份
./scripts/verify_backup.sh --all --type files
```

#### 生成验证报告

```bash
# 生成 JSON 格式的验证报告
./scripts/verify_backup.sh --all --type db --report reports/verify_report.json
```

**报告示例**:
```json
{
  "timestamp": "2026-01-29T15:00:00Z",
  "summary": {
    "total_checked": 12,
    "total_passed": 11,
    "total_failed": 1,
    "success_rate": 91.67
  },
  "failed_files": [
    "backups/db/contenthub_20260125_020000.db.gz"
  ]
}
```

#### 仅显示失败的文件

```bash
./scripts/verify_backup.sh --all --type db --failed-only
```

---

## 恢复流程

### 数据库恢复

#### 方式 1: 使用 backup_db.sh 恢复

```bash
./scripts/backup_db.sh --restore backups/db/contenthub_20260129.db.gz
```

**恢复步骤**:
1. 验证 MD5 校验和
2. 备份当前数据库（到 `contenthub_before_restore_*.db.gz`）
3. 解压备份文件
4. 验证数据库完整性
5. 提示用户停止应用
6. 替换数据库文件

**注意**: 恢复前请确保应用已停止！

#### 方式 2: 手动恢复

```bash
# 1. 停止应用
# pkill -f "python main.py" 或停止 systemd 服务

# 2. 备份当前数据库
cp data/contenthub.db data/contenthub.db.backup

# 3. 解压并恢复
gunzip -c backups/db/contenthub_20260129.db.gz > data/contenthub.db

# 4. 验证数据库完整性
sqlite3 data/contenthub.db "PRAGMA integrity_check;"

# 5. 启动应用
# python main.py 或启动 systemd 服务
```

#### 方式 3: 恢复到临时位置

```bash
# 解压到临时位置
gunzip -c backups/db/contenthub_20260129.db.gz > /tmp/contenthub_restore.db

# 验证
sqlite3 /tmp/contenthub_restore.db "SELECT * FROM accounts LIMIT 10;"

# 如果验证通过，替换原数据库
mv /tmp/contenthub_restore.db data/contenthub.db
```

### 文件恢复

```bash
# 1. 创建临时目录
mkdir -p /tmp/restore

# 2. 解压备份文件
cd /tmp/restore
tar -xzf /path/to/backups/files/files_20260129_full.tar.gz

# 3. 查看内容
ls -la /tmp/restore

# 4. 恢复到原位置
cp -r /tmp/restore/* /path/to/src/backend/

# 5. 验证
ls -la accounts/
ls -la uploads/
```

---

## 备份文件管理

### 备份目录结构

```
src/backend/
├── backups/
│   ├── db/
│   │   ├── contenthub_YYYYMMDD_HHMMSS.db.gz
│   │   ├── contenthub_YYYYMMDD_HHMMSS.db.gz.md5
│   │   ├── old/              # 30 天前的备份归档
│   │   └── failed/           # 验证失败的备份
│   └── files/
│       ├── files_YYYYMMDD_HHMMSS_full.tar.gz
│       ├── files_YYYYMMDD_HHMMSS_full.tar.gz.manifest
│       ├── files_YYYYMMDD_HHMMSS_incremental.tar.gz
│       ├── files_YYYYMMDD_HHMMSS_incremental.tar.gz.manifest
│       ├── old/              # 30 天前的备份归档
│       └── failed/           # 验证失败的备份
├── logs/
│   └── backup.log            # 备份日志
└── reports/
    └── verify_report.json    # 验证报告
```

### 磁盘空间管理

#### 查看备份占用空间

```bash
# 数据库备份
du -sh backups/db/

# 文件备份
du -sh backups/files/

# 总计
du -sh backups/
```

#### 手动清理

```bash
# 删除所有 old/ 目录中的备份
rm -rf backups/db.old/*
rm -rf backups/files/old/*

# 删除所有 failed/ 目录中的备份
rm -rf backups/db/failed/*
rm -rf backups/files/failed/*
```

#### 压缩归档备份

```bash
# 压缩 old/ 目录
cd backups/db/old
tar -czf ../archive_$(date +%Y%m).tar.gz .
cd ../..

# 删除已归档的文件
rm -rf old/*
```

---

## 常见问题排查

### 问题 1: 备份失败 - "数据库被锁定"

**原因**: 应用正在使用数据库

**解决方案**:
```bash
# 方式 1: 停止应用后再备份
pkill -f "python main.py"
./scripts/backup_db.sh --type full

# 方式 2: 使用在线备份（推荐）
# backup_db.sh 已使用 SQLite 的 .backup 命令支持在线备份
```

### 问题 2: 定时任务未执行

**检查步骤**:
```bash
# 1. 检查 cron 服务是否运行
pgrep cron

# macOS
sudo launchctl list | grep cron

# Linux
sudo systemctl status cron

# 2. 查看 cron 日志
grep CRON /var/log/syslog  # Linux
log show --predicate 'process == "cron"'  # macOS

# 3. 查看 crontab
crontab -l

# 4. 检查脚本权限
ls -l scripts/backup_db.sh
chmod +x scripts/backup_db.sh

# 5. 测试脚本
./scripts/backup_db.sh --type full
```

### 问题 3: 备份文件损坏

**检查和修复**:
```bash
# 1. 验证备份
./scripts/verify_backup.sh --file backups/db/contenthub_20260129.db.gz

# 2. 查看 MD5 校验和
cat backups/db/contenthub_20260129.db.gz.md5
md5 -q backups/db/contenthub_20260129.db.gz

# 3. 测试压缩文件
gzip -t backups/db/contenthub_20260129.db.gz

# 4. 如果损坏，使用上一个备份
./scripts/backup_db.sh --restore backups/db/contenthub_20260128.db.gz
```

### 问题 4: 磁盘空间不足

**解决方案**:
```bash
# 1. 清理旧备份
./scripts/backup_db.sh --clean
./scripts/backup_files.sh --clean

# 2. 删除 old/ 目录
rm -rf backups/db/old/*
rm -rf backups/files/old/*

# 3. 压缩归档
cd backups/db
tar -czf archive.tar.gz old/
rm -rf old/

# 4. 检查可用空间
df -h backups/
```

### 问题 5: 恢复后应用无法启动

**排查步骤**:
```bash
# 1. 验证数据库完整性
sqlite3 data/contenthub.db "PRAGMA integrity_check;"

# 2. 检查数据库表
sqlite3 data/contenthub.db ".tables"

# 3. 检查数据库权限
ls -l data/contenthub.db
chmod 644 data/contenthub.db

# 4. 查看应用日志
tail -f logs/app.log

# 5. 如果有问题，恢复备份
cp data/contenthub.db.before_restore data/contenthub.db
```

---

## 最佳实践

### 1. 定期验证备份

```bash
# 每周验证所有备份
./scripts/verify_backup.sh --all --type db
./scripts/verify_backup.sh --all --type files
```

### 2. 保留多个备份版本

- 至少保留 7 个每日备份
- 至少保留 4 个每周备份
- 至少保留 3 个每月备份

### 3. 异地备份

```bash
# 复制备份到远程服务器
rsync -avz backups/ user@remote-server:/path/to/backups/

# 或使用 AWS S3
aws s3 sync backups/ s3://my-bucket/contenthub-backups/
```

### 4. 测试恢复流程

```bash
# 每月测试一次恢复流程
# 1. 恢复到测试环境
./scripts/backup_db.sh --restore backups/db/contenthub_latest.db.gz

# 2. 验证数据完整性
sqlite3 data/contenthub.db "SELECT COUNT(*) FROM contents;"

# 3. 启动应用并测试功能
```

### 5. 监控备份状态

```bash
# 创建监控脚本
cat > scripts/check_backup.sh << 'EOF'
#!/bin/bash
# 检查最近 24 小时内是否有备份
latest_backup=$(find backups/db -name "*.db.gz" -mtime -1 | wc -l)
if [ $latest_backup -eq 0 ]; then
    echo "警告: 最近 24 小时内没有数据库备份!"
    # 发送告警通知
fi
EOF

chmod +x scripts/check_backup.sh

# 添加到 crontab
0 8 * * * /path/to/scripts/check_backup.sh
```

### 6. 备份加密

```bash
# 使用 GPG 加密备份
./scripts/backup_db.sh --type full
gpg --symmetric --cipher-algo AES256 backups/db/contenthub_20260129.db.gz
rm backups/db/contenthub_20260129.db.gz

# 解密
gpg --decrypt backups/db/contenthub_20260129.db.gz.gpg > contenthub_20260129.db.gz
```

---

## 附录

### 备份脚本命令参考

#### backup_db.sh

```bash
--type full           # 全量备份
--type incremental    # 增量备份
--list                # 列出备份
--restore FILE        # 恢复备份
--clean               # 清理旧备份
--help                # 帮助信息
```

#### backup_files.sh

```bash
--source DIR          # 指定源目录
--full                # 完整备份
--incremental         # 增量备份
--dest DIR            # 指定目标目录
--list                # 列出备份
--clean               # 清理旧备份
--help                # 帮助信息
```

#### cron_backup_setup.sh

```bash
--install             # 安装定时任务
--uninstall           # 卸载定时任务
--list                # 查看定时任务
--status              # 查看服务状态
--enable-db-full      # 启用数据库全量备份
--enable-db-incremental  # 启用数据库增量备份
--enable-files        # 启用文件备份
--disable-all         # 禁用所有任务
--test                # 测试配置
--help                # 帮助信息
```

#### verify_backup.sh

```bash
--file FILE           # 验证指定文件
--all                 # 验证所有备份
--type TYPE           # 备份类型 (db/files)
--report FILE         # 生成报告
--failed-only         # 仅显示失败文件
--help                # 帮助信息
```

### 相关文件位置

| 文件 | 路径 |
|------|------|
| 数据库 | `src/backend/data/contenthub.db` |
| 数据库备份 | `src/backend/backups/db/` |
| 文件备份 | `src/backend/backups/files/` |
| 备份日志 | `src/backend/logs/backup.log` |
| 验证报告 | `src/backend/reports/` |
| 备份脚本 | `src/backend/scripts/backup_*.sh` |

---

## 联系支持

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [ContentHub Issues](https://github.com/your-org/content-hub/issues)
- 邮件: support@contenthub.example.com

---

**文档版本**: 1.0
**最后更新**: 2026-01-29
**作者**: Claude Code
