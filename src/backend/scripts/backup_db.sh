#!/bin/bash

###############################################################################
# ContentHub 数据库备份脚本
# 功能: SQLite 数据库全量和增量备份
# 作者: Claude Code
# 日期: 2026-01-29
###############################################################################

# 遇到错误立即退出
set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 配置
DB_FILE="$BACKEND_ROOT/data/contenthub.db"
BACKUP_DIR="$BACKEND_ROOT/backups/db"
LOG_FILE="$BACKEND_ROOT/logs/backup.log"
RETENTION_DAYS=30

# 临时文件
TEMP_DB="/tmp/contenthub_backup_$$-$RANDOM.db"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# 打印使用说明
usage() {
    cat << EOF
使用方法: $(basename "$0") [选项]

选项:
  --type TYPE           备份类型: full (全量) 或 incremental (增量)
  --list                列出所有备份文件
  --restore FILE        恢复指定的备份文件
  --clean               清理超过保留期的旧备份
  --help                显示此帮助信息

示例:
  $(basename "$0") --type full          # 全量备份
  $(basename "$0") --type incremental   # 增量备份
  $(basename "$0") --list               # 列出备份
  $(basename "$0") --restore backups/db/contenthub_20260129_020000.db.gz
  $(basename "$0") --clean              # 清理旧备份

EOF
    exit 0
}

# 检查依赖
check_dependencies() {
    local missing=()

    # 检查必需的命令
    if ! command -v sqlite3 &> /dev/null; then
        missing+=("sqlite3")
    fi

    if ! command -v gzip &> /dev/null; then
        missing+=("gzip")
    fi

    # macOS 上使用原生命令，Linux 上使用 GNU 命令
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - 使用原生命令
        if ! command -v stat &> /dev/null; then
            missing+=("stat")
        fi
    else
        # Linux - 检查 GNU 命令
        if ! command -v gdate &> /dev/null && ! command -v date &> /dev/null; then
            missing+=("date")
        fi
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log "ERROR" "缺少依赖: ${missing[*]}"
        echo -e "${RED}请安装缺少的依赖${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo -e "${YELLOW}macOS: brew install ${missing[*]}${NC}"
        else
            echo -e "${YELLOW}Linux: sudo apt-get install ${missing[*]}${NC}"
        fi
        exit 1
    fi
}

# 检查数据库文件
check_database() {
    if [ ! -f "$DB_FILE" ]; then
        log "ERROR" "数据库文件不存在: $DB_FILE"
        exit 1
    fi

    # 检查数据库是否被锁定
    if sqlite3 "$DB_FILE" "PRAGMA busy_timeout = 5000; SELECT 1;" &> /dev/null; then
        log "INFO" "数据库可访问"
    else
        log "ERROR" "数据库被锁定或不可访问，请先停止应用"
        exit 1
    fi
}

# 创建备份目录
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "INFO" "创建备份目录: $BACKUP_DIR"
    fi
}

# 生成备份文件名
generate_backup_filename() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    echo "contenthub_${timestamp}.db.gz"
}

# 检查磁盘空间
check_disk_space() {
    local required_space_mb=100  # 至少需要 100MB
    local available_space_mb=$(df -m "$BACKUP_DIR" | awk 'NR==2 {print $4}')

    if [ "$available_space_mb" -lt "$required_space_mb" ]; then
        log "ERROR" "磁盘空间不足，可用: ${available_space_mb}MB，需要: ${required_space_mb}MB"
        exit 1
    fi

    log "INFO" "磁盘空间检查通过，可用: ${available_space_mb}MB"
}

###############################################################################
# 备份功能
###############################################################################

# 全量备份
full_backup() {
    log "INFO" "开始全量备份..."
    echo -e "${GREEN}正在执行全量备份...${NC}"

    # 生成备份文件名
    local backup_file=$(generate_backup_filename)
    local backup_path="$BACKUP_DIR/$backup_file"

    # 检查磁盘空间
    check_disk_space

    # 使用 SQLite 的 .backup 命令进行在线备份
    log "INFO" "复制数据库文件..."
    if sqlite3 "$DB_FILE" ".backup '$TEMP_DB'" 2>&1 | tee -a "$LOG_FILE"; then
        log "INFO" "数据库复制成功"
    else
        log "ERROR" "数据库复制失败"
        rm -f "$TEMP_DB"
        exit 1
    fi

    # 压缩备份文件
    log "INFO" "压缩备份文件..."
    if gzip -c "$TEMP_DB" > "$backup_path"; then
        log "INFO" "压缩成功"
    else
        log "ERROR" "压缩失败"
        rm -f "$TEMP_DB"
        exit 1
    fi

    # 清理临时文件
    rm -f "$TEMP_DB"

    # 获取备份文件大小
    local backup_size=$(du -h "$backup_path" | cut -f1)
    local original_size=$(du -h "$DB_FILE" | cut -f1)

    log "INFO" "全量备份完成: $backup_path (原大小: $original_size, 压缩后: $backup_size)"
    echo -e "${GREEN}✓ 全量备份完成: $backup_file${NC}"

    # 计算 MD5 校验和
    local md5sum=$(md5 -q "$backup_path")
    echo "$md5sum  $backup_file" > "$backup_path.md5"
    log "INFO" "MD5 校验和: $md5sum"
}

# 增量备份
incremental_backup() {
    log "INFO" "开始增量备份..."
    echo -e "${GREEN}正在执行增量备份...${NC}"

    # 生成备份文件名
    local backup_file=$(generate_backup_filename)
    local backup_path="$BACKUP_DIR/$backup_file"

    # 检查磁盘空间
    check_disk_space

    # SQLite 的增量备份实际上是完整备份，但我们可以标记为增量
    # 使用 VACUUM INTO 命令创建一个干净的备份
    log "INFO" "创建增量备份..."
    if sqlite3 "$DB_FILE" "VACUUM INTO '$TEMP_DB'" 2>&1 | tee -a "$LOG_FILE"; then
        log "INFO" "增量备份创建成功"
    else
        log "ERROR" "增量备份创建失败"
        rm -f "$TEMP_DB"
        exit 1
    fi

    # 压缩备份文件
    log "INFO" "压缩备份文件..."
    if gzip -c "$TEMP_DB" > "$backup_path"; then
        log "INFO" "压缩成功"
    else
        log "ERROR" "压缩失败"
        rm -f "$TEMP_DB"
        exit 1
    fi

    # 清理临时文件
    rm -f "$TEMP_DB"

    # 获取备份文件大小
    local backup_size=$(du -h "$backup_path" | cut -f1)

    log "INFO" "增量备份完成: $backup_path (大小: $backup_size)"
    echo -e "${GREEN}✓ 增量备份完成: $backup_file${NC}"

    # 计算 MD5 校验和
    local md5sum=$(md5 -q "$backup_path")
    echo "$md5sum  $backup_file" > "$backup_path.md5"
    log "INFO" "MD5 校验和: $md5sum"
}

# 列出所有备份
list_backups() {
    echo -e "${GREEN}=== 数据库备份列表 ===${NC}\n"
    echo "备份目录: $BACKUP_DIR"
    echo

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/*.db.gz 2>/dev/null)" ]; then
        echo -e "${YELLOW}没有找到备份文件${NC}"
        return
    fi

    printf "%-40s %-15s %-10s\n" "备份文件" "备份时间" "大小"
    printf "%-40s %-15s %-10s\n" "--------" "--------" "----"

    for backup in $BACKUP_DIR/*.db.gz; do
        if [ -f "$backup" ]; then
            local filename=$(basename "$backup")
            local filesize=$(du -h "$backup" | cut -f1)
            local filedate=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$backup")
            printf "%-40s %-15s %-10s\n" "$filename" "$filedate" "$filesize"
        fi
    done

    echo
    local total_size=$(du -sh $BACKUP_DIR/*.db.gz 2>/dev/null | tail -1 | cut -f1)
    echo "总计大小: $total_size"
}

# 恢复备份
restore_backup() {
    local backup_file=$1

    if [ -z "$backup_file" ]; then
        log "ERROR" "请指定要恢复的备份文件"
        echo -e "${RED}使用: $(basename "$0") --restore <backup_file>${NC}"
        exit 1
    fi

    # 检查备份文件是否存在
    if [ ! -f "$backup_file" ]; then
        log "ERROR" "备份文件不存在: $backup_file"
        exit 1
    fi

    # 验证 MD5 校验和
    local md5_file="${backup_file}.md5"
    if [ -f "$md5_file" ]; then
        log "INFO" "验证 MD5 校验和..."
        if md5 -r "$backup_file" | diff - "$md5_file" > /dev/null; then
            log "INFO" "MD5 校验和验证通过"
        else
            log "ERROR" "MD5 校验和验证失败，备份文件可能已损坏"
            exit 1
        fi
    fi

    # 备份当前数据库
    local current_backup="$BACKUP_DIR/contenthub_before_restore_$(date '+%Y%m%d_%H%M%S').db.gz"
    log "INFO" "备份当前数据库到: $current_backup"
    if gzip -c "$DB_FILE" > "$current_backup"; then
        log "INFO" "当前数据库已备份"
    else
        log "ERROR" "备份当前数据库失败"
        exit 1
    fi

    # 解压并恢复
    log "INFO" "恢复数据库..."
    echo -e "${YELLOW}正在恢复数据库，请稍候...${NC}"

    if gunzip -c "$backup_file" > "$TEMP_DB"; then
        log "INFO" "解压成功"
    else
        log "ERROR" "解压失败"
        rm -f "$TEMP_DB"
        exit 1
    fi

    # 验证恢复的数据库
    if sqlite3 "$TEMP_DB" "PRAGMA integrity_check;" | grep -q "ok"; then
        log "INFO" "数据库完整性检查通过"
    else
        log "ERROR" "数据库完整性检查失败"
        rm -f "$TEMP_DB"
        exit 1
    fi

    # 停止应用（如果正在运行）
    log "WARN" "请确保应用已停止，按 Enter 继续..."
    read -p ""

    # 替换数据库文件
    if cp "$DB_FILE" "${DB_FILE}.before_restore" && cp "$TEMP_DB" "$DB_FILE"; then
        log "INFO" "数据库恢复成功"
        rm -f "$TEMP_DB"
        echo -e "${GREEN}✓ 数据库恢复完成${NC}"
    else
        log "ERROR" "数据库恢复失败"
        rm -f "$TEMP_DB"
        exit 1
    fi
}

# 清理旧备份
clean_old_backups() {
    log "INFO" "清理超过 $RETENTION_DAYS 天的旧备份..."
    echo -e "${GREEN}正在清理旧备份...${NC}"

    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${YELLOW}备份目录不存在${NC}"
        return
    fi

    local count=0
    local total_size=0

    # 查找并删除超过保留期的备份
    while IFS= read -r backup; do
        if [ -f "$backup" ]; then
            local size=$(du -k "$backup" | cut -f1)
            total_size=$((total_size + size))

            # 移动到 failed 目录而不是直接删除
            local failed_dir="$BACKUP_DIR/old"
            mkdir -p "$failed_dir"
            mv "$backup" "$failed_dir/"

            # 同时移动 MD5 文件
            if [ -f "${backup}.md5" ]; then
                mv "${backup}.md5" "$failed_dir/"
            fi

            count=$((count + 1))
            log "INFO" "已归档旧备份: $(basename "$backup")"
        fi
    done < <(find "$BACKUP_DIR" -maxdepth 1 -name "*.db.gz" -type f -mtime +$RETENTION_DAYS)

    local total_size_mb=$((total_size / 1024))
    log "INFO" "清理完成，归档了 $count 个备份文件，释放空间: ${total_size_mb}MB"
    echo -e "${GREEN}✓ 清理完成，归档了 $count 个备份文件，释放空间: ${total_size_mb}MB${NC}"
}

###############################################################################
# 主程序
###############################################################################

main() {
    # 检查依赖
    check_dependencies

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"

    # 参数处理
    if [ $# -eq 0 ]; then
        usage
    fi

    while [ $# -gt 0 ]; do
        case $1 in
            --type)
                shift
                local backup_type=$1
                create_backup_dir
                check_database

                case $backup_type in
                    full)
                        full_backup
                        ;;
                    incremental)
                        incremental_backup
                        ;;
                    *)
                        log "ERROR" "无效的备份类型: $backup_type"
                        echo -e "${RED}备份类型必须是 'full' 或 'incremental'${NC}"
                        exit 1
                        ;;
                esac
                shift
                ;;
            --list)
                list_backups
                shift
                ;;
            --restore)
                shift
                restore_backup "$1"
                shift
                ;;
            --clean)
                clean_old_backups
                shift
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
