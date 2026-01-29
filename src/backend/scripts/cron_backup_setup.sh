#!/bin/bash

###############################################################################
# ContentHub 定时备份配置脚本
# 功能: 配置和管理 crontab 定时备份任务
# 作者: Claude Code
# 日期: 2026-01-29
###############################################################################

# 遇到错误立即退出
set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 配置
BACKUP_DB_SCRIPT="$SCRIPT_DIR/backup_db.sh"
BACKUP_FILES_SCRIPT="$SCRIPT_DIR/backup_files.sh"
LOG_FILE="$BACKEND_ROOT/logs/backup.log"
CRON_COMMENT="# ContentHub 自动备份任务"
CRON_FILE="$BACKUP_ROOT/scripts/.crontab"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# 辅助函数
###############################################################################

# 日志函数
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] [CRON] $message"
}

# 打印使用说明
usage() {
    cat << EOF
使用方法: $(basename "$0") [选项]

选项:
  --install              安装定时备份任务
  --uninstall            卸载定时备份任务
  --list                 查看当前的定时任务
  --status               查看备份服务状态
  --enable-db-full       启用数据库全量备份（每天凌晨 2 点）
  --enable-db-incremental 启用数据库增量备份（每 4 小时）
  --enable-files         启用文件备份（每天凌晨 3 点）
  --disable-all          禁用所有定时任务
  --test                 测试定时任务配置（不安装）
  --help                 显示此帮助信息

定时任务说明:
  数据库全量备份:   每天凌晨 2:00 执行
  数据库增量备份:   每 4 小时执行一次 (2:00, 6:00, 10:00, 14:00, 18:00, 22:00)
  文件备份:         每天凌晨 3:00 执行
  备份日志:         $LOG_FILE

示例:
  $(basename "$0") --install              # 安装所有定时任务
  $(basename "$0") --list                 # 查看当前定时任务
  $(basename "$0") --status               # 查看服务状态
  $(basename "$0") --enable-db-full       # 仅启用数据库全量备份
  $(basename "$0") --disable-all          # 禁用所有定时任务

EOF
    exit 0
}

# 检查依赖
check_dependencies() {
    if ! command -v crontab &> /dev/null; then
        log "ERROR" "crontab 命令未找到"
        echo -e "${RED}请确保系统已安装 cron 服务${NC}"
        exit 1
    fi

    # 检查备份脚本是否存在
    if [ ! -f "$BACKUP_DB_SCRIPT" ]; then
        log "ERROR" "数据库备份脚本不存在: $BACKUP_DB_SCRIPT"
        exit 1
    fi

    if [ ! -f "$BACKUP_FILES_SCRIPT" ]; then
        log "ERROR" "文件备份脚本不存在: $BACKUP_FILES_SCRIPT"
        exit 1
    fi
}

# 检查脚本权限
check_script_permissions() {
    log "INFO" "检查脚本权限..."

    if [ ! -x "$BACKUP_DB_SCRIPT" ]; then
        log "WARN" "数据库备份脚本没有执行权限，正在添加..."
        chmod +x "$BACKUP_DB_SCRIPT"
    fi

    if [ ! -x "$BACKUP_FILES_SCRIPT" ]; then
        log "WARN" "文件备份脚本没有执行权限，正在添加..."
        chmod +x "$BACKUP_FILES_SCRIPT"
    fi

    log "INFO" "脚本权限检查完成"
}

# 创建必要的目录
create_directories() {
    log "INFO" "创建必要的目录..."

    mkdir -p "$BACKEND_ROOT/logs"
    mkdir -p "$BACKEND_ROOT/backups/db"
    mkdir -p "$BACKEND_ROOT/backups/files"

    log "INFO" "目录创建完成"
}

# 生成 crontab 配置
generate_crontab() {
    cat << EOF
$CRON_COMMENT
# 数据库全量备份 - 每天凌晨 2:00
0 2 * * * $BACKUP_DB_SCRIPT --type full >> $LOG_FILE 2>&1

# 数据库增量备份 - 每 4 小时 (2:00, 6:00, 10:00, 14:00, 18:00, 22:00)
# 注意: 2:00 的增量备份会被全量备份替代，这里配置其他时间点
0 6,10,14,18,22 * * * $BACKUP_DB_SCRIPT --type incremental >> $LOG_FILE 2>&1

# 文件备份 - 每天凌晨 3:00
0 3 * * * $BACKUP_FILES_SCRIPT --full >> $LOG_FILE 2>&1

# 清理旧备份 - 每周日凌晨 4:00
0 4 * * 0 $BACKUP_DB_SCRIPT --clean >> $LOG_FILE 2>&1
0 5 * * 0 $BACKUP_FILES_SCRIPT --clean >> $LOG_FILE 2>&1

EOF
}

# 安装定时任务
install_cron() {
    log "INFO" "安装定时备份任务..."
    echo -e "${GREEN}正在安装定时任务...${NC}"

    # 检查依赖
    check_dependencies

    # 检查脚本权限
    check_script_permissions

    # 创建必要的目录
    create_directories

    # 生成 crontab 配置
    local new_cron=$(generate_crontab)

    # 保存到临时文件
    echo "$new_cron" > "$CRON_FILE"

    # 添加到现有的 crontab
    local current_cron=$(crontab -l 2>/dev/null || true)

    # 移除旧的 ContentHub 任务
    local cleaned_cron=$(echo "$current_cron" | grep -v "$CRON_COMMENT" || true)

    # 合并新的定时任务
    {
        echo "$cleaned_cron"
        echo "$new_cron"
    } | crontab -

    log "INFO" "定时任务安装成功"
    echo -e "${GREEN}✓ 定时任务安装成功${NC}"
    echo
    echo -e "${BLUE}已安装的定时任务:${NC}"
    list_cron
}

# 卸载定时任务
uninstall_cron() {
    log "INFO" "卸载定时备份任务..."
    echo -e "${YELLOW}正在卸载定时任务...${NC}"

    # 获取当前的 crontab
    local current_cron=$(crontab -l 2>/dev/null || true)

    # 移除 ContentHub 任务
    local cleaned_cron=$(echo "$current_cron" | grep -v "$CRON_COMMENT" || true)

    # 更新 crontab
    echo "$cleaned_cron" | crontab -

    log "INFO" "定时任务卸载成功"
    echo -e "${GREEN}✓ 定时任务已卸载${NC}"

    # 删除临时文件
    if [ -f "$CRON_FILE" ]; then
        rm -f "$CRON_FILE"
    fi
}

# 列出定时任务
list_cron() {
    echo -e "${BLUE}=== ContentHub 定时备份任务 ===${NC}\n"

    local current_cron=$(crontab -l 2>/dev/null || true)
    local contenthub_cron=$(echo "$current_cron" | grep -A 100 "$CRON_COMMENT" | grep -v "^$CRON_COMMENT" || true)

    if [ -z "$contenthub_cron" ]; then
        echo -e "${YELLOW}未安装定时备份任务${NC}"
        echo
        echo -e "使用 ${GREEN}$(basename "$0") --install${NC} 安装定时任务"
        return
    fi

    echo "定时任务列表:"
    echo
    echo "$contenthub_cron" | while read -r line; do
        if [ -n "$line" ]; then
            # 解析 crontab 时间
            local cron_time=$(echo "$line" | awk '{print $1, $2, $3, $4, $5}')
            local cron_cmd=$(echo "$line" | awk '{for(i=6;i<=NF;i++)printf $i" "; print ""}')

            # 格式化输出
            echo -e "  ${GREEN}时间:${NC} $cron_time"
            echo -e "  ${GREEN}命令:${NC} $cron_cmd"
            echo
        fi
    done

    echo -e "${BLUE}备份日志:${NC} $LOG_FILE"
    echo -e "${BLUE}配置文件:${NC} $CRON_FILE"
}

# 查看服务状态
check_status() {
    echo -e "${BLUE}=== 备份服务状态 ===${NC}\n"

    # 检查 cron 服务是否运行
    if pgrep -x "cron" > /dev/null || pgrep -x "crond" > /dev/null; then
        echo -e "${GREEN}✓ Cron 服务状态: 运行中${NC}"
    else
        echo -e "${RED}✗ Cron 服务状态: 未运行${NC}"
        echo
        echo -e "${YELLOW}启动 cron 服务:${NC}"
        echo "  macOS: sudo launchctl load -w /System/Library/LaunchDaemons/com.vix.cron.plist"
        echo "  Linux: sudo systemctl start cron"
        return
    fi

    echo

    # 检查定时任务是否安装
    local current_cron=$(crontab -l 2>/dev/null || true)
    if echo "$current_cron" | grep -q "$CRON_COMMENT"; then
        echo -e "${GREEN}✓ 定时任务状态: 已安装${NC}"
    else
        echo -e "${RED}✗ 定时任务状态: 未安装${NC}"
    fi

    echo

    # 检查备份目录
    if [ -d "$BACKEND_ROOT/backups/db" ]; then
        local db_count=$(find "$BACKEND_ROOT/backups/db" -maxdepth 1 -name "*.db.gz" -type f | wc -l)
        echo -e "${GREEN}✓ 数据库备份: $db_count 个文件${NC}"
    else
        echo -e "${RED}✗ 数据库备份目录不存在${NC}"
    fi

    if [ -d "$BACKEND_ROOT/backups/files" ]; then
        local files_count=$(find "$BACKEND_ROOT/backups/files" -maxdepth 1 -name "*.tar.gz" -type f | wc -l)
        echo -e "${GREEN}✓ 文件备份: $files_count 个文件${NC}"
    else
        echo -e "${RED}✗ 文件备份目录不存在${NC}"
    fi

    echo

    # 检查最近的备份
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}最近 5 条备份日志:${NC}"
        tail -5 "$LOG_FILE" | while read -r line; do
            echo "  $line"
        done
    else
        echo -e "${YELLOW}备份日志文件不存在${NC}"
    fi

    echo

    # 检查磁盘空间
    local available_space=$(df -h "$BACKEND_ROOT/backups" | awk 'NR==2 {print $4}')
    echo -e "${BLUE}备份目录可用空间:${NC} $available_space"
}

# 启用特定任务
enable_task() {
    local task=$1

    log "INFO" "启用任务: $task"
    echo -e "${GREEN}正在启用任务: $task${NC}"

    case $task in
        db-full)
            local cron_entry="0 2 * * * $BACKUP_DB_SCRIPT --type full >> $LOG_FILE 2>&1"
            add_cron_entry "$cron_entry" "数据库全量备份"
            ;;
        db-incremental)
            local cron_entry="0 6,10,14,18,22 * * * $BACKUP_DB_SCRIPT --type incremental >> $LOG_FILE 2>&1"
            add_cron_entry "$cron_entry" "数据库增量备份"
            ;;
        files)
            local cron_entry="0 3 * * * $BACKUP_FILES_SCRIPT --full >> $LOG_FILE 2>&1"
            add_cron_entry "$cron_entry" "文件备份"
            ;;
        *)
            log "ERROR" "未知任务类型: $task"
            echo -e "${RED}任务类型必须是: db-full, db-incremental, files${NC}"
            exit 1
            ;;
    esac
}

# 添加 crontab 条目
add_cron_entry() {
    local cron_entry=$1
    local task_name=$2

    # 获取当前 crontab
    local current_cron=$(crontab -l 2>/dev/null || true)

    # 检查是否已存在
    if echo "$current_cron" | grep -qF "$cron_entry"; then
        echo -e "${YELLOW}⚠ 任务已存在: $task_name${NC}"
        return
    fi

    # 添加新任务
    (echo "$current_cron"; echo "$CRON_COMMENT"; echo "$cron_entry") | crontab -

    log "INFO" "任务添加成功: $task_name"
    echo -e "${GREEN}✓ 任务已启用: $task_name${NC}"
}

# 禁用所有任务
disable_all() {
    log "INFO" "禁用所有定时备份任务..."
    echo -e "${YELLOW}正在禁用所有定时任务...${NC}"

    uninstall_cron

    echo -e "${GREEN}✓ 所有定时任务已禁用${NC}"
}

# 测试定时任务配置
test_cron() {
    echo -e "${BLUE}=== 测试定时任务配置 ===${NC}\n"

    check_dependencies
    check_script_permissions
    create_directories

    echo -e "${GREEN}✓ 依赖检查通过${NC}"
    echo -e "${GREEN}✓ 脚本权限检查通过${NC}"
    echo -e "${GREEN}✓ 目录创建成功${NC}"
    echo

    echo -e "${BLUE}生成的 crontab 配置:${NC}"
    echo
    generate_crontab

    echo
    echo -e "${YELLOW}使用 --install 安装此配置${NC}"
}

###############################################################################
# 主程序
###############################################################################

main() {
    # 参数处理
    if [ $# -eq 0 ]; then
        usage
    fi

    while [ $# -gt 0 ]; do
        case $1 in
            --install)
                install_cron
                exit 0
                ;;
            --uninstall)
                uninstall_cron
                exit 0
                ;;
            --list)
                list_cron
                exit 0
                ;;
            --status)
                check_status
                exit 0
                ;;
            --enable-db-full)
                check_dependencies
                check_script_permissions
                enable_task "db-full"
                exit 0
                ;;
            --enable-db-incremental)
                check_dependencies
                check_script_permissions
                enable_task "db-incremental"
                exit 0
                ;;
            --enable-files)
                check_dependencies
                check_script_permissions
                enable_task "files"
                exit 0
                ;;
            --disable-all)
                disable_all
                exit 0
                ;;
            --test)
                test_cron
                exit 0
                ;;
            --help|-h)
                usage
                ;;
            *)
                log "ERROR" "未知选项: $1"
                usage
                ;;
        esac
    done
}

# 运行主程序
main "$@"
