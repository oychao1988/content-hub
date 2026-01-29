#!/bin/bash

###############################################################################
# ContentHub 文件备份脚本
# 功能: 内容文件和图片文件的增量备份
# 作者: Claude Code
# 日期: 2026-01-29
###############################################################################

# 遇到错误立即退出
set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 配置
DEFAULT_SOURCES=("$BACKEND_ROOT/accounts" "$BACKEND_ROOT/uploads")
BACKUP_DIR="$BACKEND_ROOT/backups/files"
LOG_FILE="$BACKEND_ROOT/logs/backup.log"
RETENTION_DAYS=30

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
    echo "[$timestamp] [$level] [FILES] $message" | tee -a "$LOG_FILE"
}

# 打印使用说明
usage() {
    cat << EOF
使用方法: $(basename "$0") [选项]

选项:
  --source DIR           指定源目录（可多次使用）
  --full                 完整备份所有默认目录
  --incremental          增量备份（基于最新完整备份）
  --dest DIR             指定备份目标目录（默认: backups/files/）
  --list                 列出所有备份文件
  --clean                清理超过保留期的旧备份
  --help                 显示此帮助信息

示例:
  $(basename "$0") --full                              # 完整备份所有默认目录
  $(basename "$0") --source accounts/ --incremental    # 增量备份指定目录
  $(basename "$0") --source uploads/ --dest /tmp/backup  # 备份到指定位置
  $(basename "$0") --list                              # 列出备份

默认备份目录:
  - accounts/    (账号配置文件)
  - uploads/     (上传的图片和文件)

EOF
    exit 0
}

# 检查依赖
check_dependencies() {
    local deps=("tar" "gzip" "rsync" "find" "gstat" "gdate")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            # 尝试使用 GNU 前缀
            if ! command -v "g$dep" &> /dev/null; then
                missing+=("$dep")
            fi
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log "ERROR" "缺少依赖: ${missing[*]}"
        echo -e "${RED}请安装缺少的依赖${NC}"
        exit 1
    fi
}

# 检查源目录
check_sources() {
    local sources=("$@")
    local valid_sources=()

    for source in "${sources[@]}"; do
        # 处理相对路径
        if [[ ! "$source" = /* ]]; then
            source="$BACKEND_ROOT/$source"
        fi

        if [ -d "$source" ]; then
            valid_sources+=("$source")
            log "INFO" "添加源目录: $source"
        else
            log "WARN" "源目录不存在，跳过: $source"
        fi
    done

    if [ ${#valid_sources[@]} -eq 0 ]; then
        log "ERROR" "没有有效的源目录"
        exit 1
    fi

    echo "${valid_sources[@]}"
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
    echo "files_${timestamp}.tar.gz"
}

# 查找最新的完整备份
find_latest_full_backup() {
    local latest_backup=$(find "$BACKUP_DIR" -maxdepth 1 -name "files_*_full.tar.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2)

    if [ -n "$latest_backup" ] && [ -f "$latest_backup" ]; then
        echo "$latest_backup"
    else
        echo ""
    fi
}

# 检查磁盘空间
check_disk_space() {
    local required_space_mb=500  # 至少需要 500MB
    local available_space_mb=$(df -m "$BACKUP_DIR" | awk 'NR==2 {print $4}')

    if [ "$available_space_mb" -lt "$required_space_mb" ]; then
        log "ERROR" "磁盘空间不足，可用: ${available_space_mb}MB，需要: ${required_space_mb}MB"
        exit 1
    fi

    log "INFO" "磁盘空间检查通过，可用: ${available_space_mb}MB"
}

# 计算目录大小
calculate_size() {
    local dir=$1
    du -sm "$dir" | cut -f1
}

###############################################################################
# 备份功能
###############################################################################

# 完整备份
full_backup() {
    local sources=("$@")
    log "INFO" "开始完整备份..."
    echo -e "${GREEN}正在执行完整备份...${NC}"

    # 生成备份文件名
    local backup_file=$(generate_backup_filename)
    local backup_file_full="files_$(date '+%Y%m%d_%H%M%S')_full.tar.gz"
    local backup_path="$BACKUP_DIR/$backup_file_full"

    # 检查磁盘空间
    check_disk_space

    # 计算源目录总大小
    local total_size_mb=0
    for source in "${sources[@]}"; do
        local size=$(calculate_size "$source")
        total_size_mb=$((total_size_mb + size))
    done
    log "INFO" "源目录总大小: ${total_size_mb}MB"

    # 创建临时文件列表
    local temp_list=$(mktemp)
    for source in "${sources[@]}"; do
        # 使用相对路径，便于恢复
        local rel_path="${source#$BACKEND_ROOT/}"
        echo "$rel_path" >> "$temp_list"
    done

    # 切换到后端根目录
    cd "$BACKEND_ROOT"

    # 创建 tar.gz 压缩包
    log "INFO" "创建压缩包..."
    if tar -czf "$backup_path" -T "$temp_list" 2>&1 | tee -a "$LOG_FILE"; then
        log "INFO" "压缩包创建成功"
    else
        log "ERROR" "压缩包创建失败"
        rm -f "$temp_list"
        exit 1
    fi

    # 清理临时文件
    rm -f "$temp_list"

    # 获取备份文件大小
    local backup_size=$(du -h "$backup_path" | cut -f1)
    local compression_ratio=$((100 - (total_size_mb * 100 / $(du -m "$backup_path" | cut -f1))))

    log "INFO" "完整备份完成: $backup_path (原始: ${total_size_mb}MB, 压缩后: $backup_size)"
    echo -e "${GREEN}✓ 完整备份完成: $backup_file_full${NC}"

    # 创建备份清单
    local manifest_file="$backup_path.manifest"
    echo "备份时间: $(date '+%Y-%m-%d %H:%M:%S')" > "$manifest_file"
    echo "备份类型: 完整备份" >> "$manifest_file"
    echo "源目录:" >> "$manifest_file"
    for source in "${sources[@]}"; do
        echo "  - $source" >> "$manifest_file"
    done
    echo "原始大小: ${total_size_mb}MB" >> "$manifest_file"
    echo "压缩后大小: $backup_size" >> "$manifest_file"
    echo "压缩率: $compression_ratio%" >> "$manifest_file"

    log "INFO" "备份清单已创建: $manifest_file"
}

# 增量备份
incremental_backup() {
    local sources=("$@")
    log "INFO" "开始增量备份..."
    echo -e "${GREEN}正在执行增量备份...${NC}"

    # 查找最新的完整备份
    local latest_backup=$(find_latest_full_backup)

    if [ -z "$latest_backup" ]; then
        log "WARN" "未找到完整备份，将执行完整备份"
        full_backup "${sources[@]}"
        return
    fi

    log "INFO" "基于完整备份: $(basename "$latest_backup")"

    # 生成备份文件名
    local backup_file="files_$(date '+%Y%m%d_%H%M%S')_incremental.tar.gz"
    local backup_path="$BACKUP_DIR/$backup_file"

    # 检查磁盘空间
    check_disk_space

    # 创建临时目录用于比较
    local temp_dir=$(mktemp -d)
    mkdir -p "$temp_dir/old" "$temp_dir/new"

    # 解压最新备份到临时目录
    log "INFO" "解压最新备份进行比较..."
    tar -xzf "$latest_backup" -C "$temp_dir/old" 2>&1 | tee -a "$LOG_FILE"

    # 创建新备份的文件列表
    local temp_list=$(mktemp)
    local changed_count=0

    for source in "${sources[@]}"; do
        local rel_path="${source#$BACKEND_ROOT/}"

        # 使用 rsync 查找变化的文件
        if [ -d "$temp_dir/old/$rel_path" ]; then
            # 比较并复制变化的文件
            rsync -av --compare-dest="$temp_dir/old/$rel_path" \
                  "$source/" "$temp_dir/new/$rel_path/" 2>&1 | tee -a "$LOG_FILE"

            # 检查是否有文件变化
            if [ -n "$(find "$temp_dir/new/$rel_path" -type f)" ]; then
                changed_count=$((changed_count + $(find "$temp_dir/new/$rel_path" -type f | wc -l)))
                echo "$rel_path" >> "$temp_list"
            fi
        else
            # 目录不存在于旧备份中，完全新增
            changed_count=$((changed_count + $(find "$source" -type f | wc -l)))
            echo "$rel_path" >> "$temp_list"
        fi
    done

    # 如果没有变化，只创建一个标记文件
    if [ $changed_count -eq 0 ]; then
        log "INFO" "没有文件变化，创建空增量备份"
        echo "无变化" > "$backup_path.empty"
        rm -rf "$temp_dir" "$temp_list"
        echo -e "${YELLOW}✓ 没有文件变化${NC}"
        return
    fi

    log "INFO" "检测到 $changed_count 个文件有变化"

    # 切换到后端根目录
    cd "$BACKEND_ROOT"

    # 创建增量备份压缩包
    log "INFO" "创建增量压缩包..."
    if tar -czf "$backup_path" -T "$temp_list" 2>&1 | tee -a "$LOG_FILE"; then
        log "INFO" "增量压缩包创建成功"
    else
        log "ERROR" "增量压缩包创建失败"
        rm -rf "$temp_dir" "$temp_list"
        exit 1
    fi

    # 清理临时文件
    rm -rf "$temp_dir" "$temp_list"

    # 获取备份文件大小
    local backup_size=$(du -h "$backup_path" | cut -f1)

    log "INFO" "增量备份完成: $backup_path (大小: $backup_size, 变化文件: $changed_count)"
    echo -e "${GREEN}✓ 增量备份完成: $backup_file${NC}"

    # 创建备份清单
    local manifest_file="$backup_path.manifest"
    echo "备份时间: $(date '+%Y-%m-%d %H:%M:%S')" > "$manifest_file"
    echo "备份类型: 增量备份" >> "$manifest_file"
    echo "基于备份: $(basename "$latest_backup")" >> "$manifest_file"
    echo "变化文件数: $changed_count" >> "$manifest_file"
    echo "压缩后大小: $backup_size" >> "$manifest_file"

    log "INFO" "备份清单已创建: $manifest_file"
}

# 列出所有备份
list_backups() {
    echo -e "${GREEN}=== 文件备份列表 ===${NC}\n"
    echo "备份目录: $BACKUP_DIR"
    echo

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/*.tar.gz 2>/dev/null)" ]; then
        echo -e "${YELLOW}没有找到备份文件${NC}"
        return
    fi

    printf "%-45s %-15s %-10s %-10s\n" "备份文件" "备份时间" "类型" "大小"
    printf "%-45s %-15s %-10s %-10s\n" "--------" "--------" "----" "----"

    for backup in $BACKUP_DIR/*.tar.gz; do
        if [ -f "$backup" ]; then
            local filename=$(basename "$backup")
            local filesize=$(du -h "$backup" | cut -f1)
            local filedate=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$backup")

            # 确定备份类型
            local backup_type="未知"
            if [[ "$filename" == *"_full.tar.gz" ]]; then
                backup_type="完整"
            elif [[ "$filename" == *"_incremental.tar.gz" ]]; then
                backup_type="增量"
            fi

            printf "%-45s %-15s %-10s %-10s\n" "$filename" "$filedate" "$backup_type" "$filesize"
        fi
    done

    echo
    local total_size=$(du -sh $BACKUP_DIR/*.tar.gz 2>/dev/null | tail -1 | cut -f1)
    echo "总计大小: $total_size"
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

            # 移动到 old 目录而不是直接删除
            local old_dir="$BACKUP_DIR/old"
            mkdir -p "$old_dir"
            mv "$backup" "$old_dir/"

            # 同时移动清单文件
            if [ -f "${backup}.manifest" ]; then
                mv "${backup}.manifest" "$old_dir/"
            fi

            count=$((count + 1))
            log "INFO" "已归档旧备份: $(basename "$backup")"
        fi
    done < <(find "$BACKUP_DIR" -maxdepth 1 -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS)

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

    local sources=()
    local backup_type=""
    local custom_dest=""

    while [ $# -gt 0 ]; do
        case $1 in
            --source)
                shift
                sources+=("$1")
                shift
                ;;
            --full)
                backup_type="full"
                shift
                ;;
            --incremental)
                backup_type="incremental"
                shift
                ;;
            --dest)
                shift
                custom_dest=$1
                BACKUP_DIR="$custom_dest"
                shift
                ;;
            --list)
                list_backups
                exit 0
                ;;
            --clean)
                clean_old_backups
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

    # 如果没有指定源目录，使用默认目录
    if [ ${#sources[@]} -eq 0 ]; then
        sources=("${DEFAULT_SOURCES[@]}")
    fi

    # 验证源目录
    sources=($(check_sources "${sources[@]}"))

    # 创建备份目录
    create_backup_dir

    # 执行备份
    case $backup_type in
        full)
            full_backup "${sources[@]}"
            ;;
        incremental)
            incremental_backup "${sources[@]}"
            ;;
        *)
            log "ERROR" "请指定备份类型: --full 或 --incremental"
            echo -e "${RED}使用 --full 或 --incremental 指定备份类型${NC}"
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"
