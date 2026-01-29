#!/bin/bash

###############################################################################
# ContentHub 备份验证脚本
# 功能: 验证备份文件完整性和可恢复性
# 作者: Claude Code
# 日期: 2026-01-29
###############################################################################

# 遇到错误立即退出
set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 配置
BACKUP_DB_DIR="$BACKEND_ROOT/backups/db"
BACKUP_FILES_DIR="$BACKEND_ROOT/backups/files"
TEMP_DIR="/tmp/contenthub_verify_$$"
REPORT_DIR="$BACKEND_ROOT/reports"
LOG_FILE="$BACKEND_ROOT/logs/verify.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 验证结果统计
TOTAL_CHECKED=0
TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_FILES=()

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
  --file FILE           验证指定的备份文件
  --all                 验证所有备份文件
  --type TYPE           备份类型: db 或 files
  --report FILE         生成验证报告（JSON 格式）
  --repair              尝试修复损坏的备份文件
  --failed-only         仅显示验证失败的文件
  --help                显示此帮助信息

验证项:
  ✓ 文件存在性检查
  ✓ 文件大小验证
  ✓ MD5 校验和验证
  ✓ 压缩文件完整性测试
  ✓ 数据库完整性检查（针对数据库备份）
  ✓ 文件恢复测试（可选）

示例:
  $(basename "$0") --file backups/db/contenthub_20260129.db.gz
  $(basename "$0") --all --type db
  $(basename "$0") --all --report reports/verify_report.json
  $(basename "$0") --all --failed-only

EOF
    exit 0
}

# 检查依赖
check_dependencies() {
    local deps=("sqlite3" "gzip" "gunzip" "tar" "md5" "jq" "gstat")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log "ERROR" "缺少依赖: ${missing[*]}"
        echo -e "${RED}请安装缺少的依赖: brew install ${missing[*]}${NC}"
        exit 1
    fi
}

# 创建临时目录
create_temp_dir() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
    mkdir -p "$TEMP_DIR"
    log "INFO" "创建临时目录: $TEMP_DIR"
}

# 清理临时目录
cleanup_temp_dir() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
        log "INFO" "清理临时目录"
    fi
}

# 创建报告目录
create_report_dir() {
    if [ ! -d "$REPORT_DIR" ]; then
        mkdir -p "$REPORT_DIR"
        log "INFO" "创建报告目录: $REPORT_DIR"
    fi
}

###############################################################################
# 验证函数
###############################################################################

# 验证文件存在性
verify_file_exists() {
    local file=$1

    if [ ! -f "$file" ]; then
        log "ERROR" "文件不存在: $file"
        return 1
    fi

    log "INFO" "文件存在: $file"
    return 0
}

# 验证文件大小
verify_file_size() {
    local file=$1
    local min_size=1024  # 最小 1KB

    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)

    if [ -z "$size" ]; then
        log "ERROR" "无法获取文件大小: $file"
        return 1
    fi

    if [ "$size" -lt "$min_size" ]; then
        log "ERROR" "文件太小 ($size bytes): $file"
        return 1
    fi

    log "INFO" "文件大小正常: $file ($size bytes)"
    return 0
}

# 验证 MD5 校验和
verify_md5() {
    local file=$1
    local md5_file="${file}.md5"

    if [ ! -f "$md5_file" ]; then
        log "WARN" "MD5 文件不存在，跳过校验: $md5_file"
        return 0
    fi

    local current_md5=$(md5 -q "$file")
    local saved_md5=$(cat "$md5_file" | cut -d' ' -f1)

    if [ "$current_md5" != "$saved_md5" ]; then
        log "ERROR" "MD5 校验失败: $file"
        log "ERROR" "  当前: $current_md5"
        log "ERROR" "  保存: $saved_md5"
        return 1
    fi

    log "INFO" "MD5 校验通过: $file"
    return 0
}

# 测试压缩文件完整性
test_compression() {
    local file=$1

    if [[ "$file" == *.gz ]]; then
        if ! gzip -t "$file" 2>/dev/null; then
            log "ERROR" "Gzip 压缩文件损坏: $file"
            return 1
        fi
        log "INFO" "Gzip 压缩文件完整: $file"
    elif [[ "$file" == *.tar.gz ]]; then
        if ! tar -tzf "$file" > /dev/null 2>&1; then
            log "ERROR" "Tar 压缩文件损坏: $file"
            return 1
        fi
        log "INFO" "Tar 压缩文件完整: $file"
    fi

    return 0
}

# 验证数据库备份
verify_database_backup() {
    local file=$1

    log "INFO" "验证数据库备份: $file"

    # 解压到临时目录
    local temp_db="$TEMP_DIR/verify.db"
    if ! gunzip -c "$file" > "$temp_db" 2>/dev/null; then
        log "ERROR" "解压失败: $file"
        return 1
    fi

    # 验证数据库完整性
    if ! sqlite3 "$temp_db" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
        log "ERROR" "数据库完整性检查失败: $file"
        return 1
    fi

    # 检查数据库表
    local tables=$(sqlite3 "$temp_db" "SELECT name FROM sqlite_master WHERE type='table';" 2>/dev/null)
    if [ -z "$tables" ]; then
        log "ERROR" "数据库中没有表: $file"
        return 1
    fi

    log "INFO" "数据库验证通过: $file"
    log "INFO" "  包含表: $(echo "$tables" | tr '\n' ', ' | sed 's/,$//')"
    return 0
}

# 验证文件备份
verify_files_backup() {
    local file=$1

    log "INFO" "验证文件备份: $file"

    # 解压到临时目录
    if ! tar -xzf "$file" -C "$TEMP_DIR" 2>/dev/null; then
        log "ERROR" "解压失败: $file"
        return 1
    fi

    # 检查解压后的文件
    local file_count=$(find "$TEMP_DIR" -type f | wc -l)
    if [ "$file_count" -eq 0 ]; then
        log "ERROR" "备份中没有文件: $file"
        return 1
    fi

    log "INFO" "文件备份验证通过: $file"
    log "INFO" "  包含文件数: $file_count"
    return 0
}

# 执行完整验证
verify_backup_file() {
    local file=$1
    local backup_type=$2

    echo -e "${BLUE}验证: $(basename "$file")${NC}"

    TOTAL_CHECKED=$((TOTAL_CHECKED + 1))

    # 验证文件存在性
    if ! verify_file_exists "$file"; then
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_FILES+=("$file")
        echo -e "${RED}✗ 验证失败${NC}\n"
        return 1
    fi

    # 验证文件大小
    if ! verify_file_size "$file"; then
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_FILES+=("$file")
        echo -e "${RED}✗ 验证失败${NC}\n"
        return 1
    fi

    # 验证 MD5 校验和
    if ! verify_md5 "$file"; then
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_FILES+=("$file")
        echo -e "${RED}✗ 验证失败${NC}\n"
        return 1
    fi

    # 测试压缩文件完整性
    if ! test_compression "$file"; then
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_FILES+=("$file")
        echo -e "${RED}✗ 验证失败${NC}\n"
        return 1
    fi

    # 根据类型执行特定验证
    if [ "$backup_type" = "db" ]; then
        if ! verify_database_backup "$file"; then
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
            FAILED_FILES+=("$file")
            echo -e "${RED}✗ 验证失败${NC}\n"
            return 1
        fi
    elif [ "$backup_type" = "files" ]; then
        if ! verify_files_backup "$file"; then
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
            FAILED_FILES+=("$file")
            echo -e "${RED}✗ 验证失败${NC}\n"
            return 1
        fi
    fi

    TOTAL_PASSED=$((TOTAL_PASSED + 1))
    echo -e "${GREEN}✓ 验证通过${NC}\n"
    return 0
}

# 验证所有备份
verify_all_backups() {
    local backup_type=$1
    local backup_dir=""

    case $backup_type in
        db)
            backup_dir="$BACKUP_DB_DIR"
            ;;
        files)
            backup_dir="$BACKUP_FILES_DIR"
            ;;
        *)
            log "ERROR" "无效的备份类型: $backup_type"
            exit 1
            ;;
    esac

    if [ ! -d "$backup_dir" ]; then
        log "ERROR" "备份目录不存在: $backup_dir"
        exit 1
    fi

    echo -e "${BLUE}=== 验证所有 ${backup_type} 备份 ===${NC}\n"

    local files=$(find "$backup_dir" -maxdepth 1 -name "*.gz" -type f | sort)

    if [ -z "$files" ]; then
        echo -e "${YELLOW}没有找到备份文件${NC}"
        return
    fi

    for file in $files; do
        verify_backup_file "$file" "$backup_type"
    done
}

# 移动失败的备份到 failed 目录
move_failed_backups() {
    if [ ${#FAILED_FILES[@]} -eq 0 ]; then
        return
    fi

    log "WARN" "移动 ${#FAILED_FILES[@]} 个失败的备份到 failed 目录..."

    for file in "${FAILED_FILES[@]}"; do
        local backup_dir=$(dirname "$file")
        local failed_dir="$backup_dir/failed"
        mkdir -p "$failed_dir"

        local filename=$(basename "$file")
        mv "$file" "$failed_dir/"

        if [ -f "${file}.md5" ]; then
            mv "${file}.md5" "$failed_dir/"
        fi

        log "INFO" "已移动: $filename"
    done
}

# 生成验证报告（JSON 格式）
generate_report() {
    local report_file=$1

    create_report_dir

    log "INFO" "生成验证报告: $report_file"

    cat > "$report_file" << EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "summary": {
    "total_checked": $TOTAL_CHECKED,
    "total_passed": $TOTAL_PASSED,
    "total_failed": $TOTAL_FAILED,
    "success_rate": $(awk "BEGIN {printf \"%.2f\", ($TOTAL_PASSED/$TOTAL_CHECKED)*100}")
  },
  "failed_files": [
EOF

    local first=true
    for file in "${FAILED_FILES[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        echo -n "    \"$file\"" >> "$report_file"
    done

    cat >> "$report_file" << EOF

  ]
}
EOF

    log "INFO" "报告生成完成: $report_file"
    echo -e "${GREEN}✓ 报告已生成: $report_file${NC}"
}

# 打印验证摘要
print_summary() {
    echo
    echo -e "${BLUE}=== 验证摘要 ===${NC}"
    echo
    echo -e "总检查数: ${TOTAL_CHECKED}"
    echo -e "${GREEN}通过: ${TOTAL_PASSED}${NC}"
    echo -e "${RED}失败: ${TOTAL_FAILED}${NC}"

    if [ $TOTAL_CHECKED -gt 0 ]; then
        local success_rate=$(awk "BEGIN {printf \"%.2f\", ($TOTAL_PASSED/$TOTAL_CHECKED)*100}")
        echo -e "成功率: ${success_rate}%"
    fi

    if [ ${#FAILED_FILES[@]} -gt 0 ]; then
        echo
        echo -e "${RED}失败的文件:${NC}"
        for file in "${FAILED_FILES[@]}"; do
            echo -e "  ${RED}✗${NC} $(basename "$file")"
        done
    fi
}

###############################################################################
# 主程序
###############################################################################

main() {
    # 设置退出时清理
    trap cleanup_temp_dir EXIT

    # 检查依赖
    check_dependencies

    # 创建临时目录
    create_temp_dir

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"

    # 参数处理
    if [ $# -eq 0 ]; then
        usage
    fi

    local backup_file=""
    local verify_all=false
    local backup_type=""
    local report_file=""
    local failed_only=false

    while [ $# -gt 0 ]; do
        case $1 in
            --file)
                shift
                backup_file=$1
                ;;
            --all)
                verify_all=true
                ;;
            --type)
                shift
                backup_type=$1
                ;;
            --report)
                shift
                report_file=$1
                ;;
            --failed-only)
                failed_only=true
                ;;
            --help|-h)
                usage
                ;;
            *)
                log "ERROR" "未知选项: $1"
                usage
                ;;
        esac
        shift
    done

    # 执行验证
    if [ -n "$backup_file" ]; then
        # 验证单个文件
        if [[ "$backup_file" == *"/db/"* ]]; then
            backup_type="db"
        elif [[ "$backup_file" == *"/files/"* ]]; then
            backup_type="files"
        fi

        verify_backup_file "$backup_file" "$backup_type"
    elif [ "$verify_all" = true ]; then
        # 验证所有备份
        if [ -z "$backup_type" ]; then
            log "ERROR" "使用 --all 时必须指定 --type"
            echo -e "${RED}使用 --type db 或 --type files 指定备份类型${NC}"
            exit 1
        fi

        verify_all_backups "$backup_type"
    else
        log "ERROR" "请指定 --file 或 --all"
        usage
    fi

    # 移动失败的备份
    if [ ${#FAILED_FILES[@]} -gt 0 ]; then
        move_failed_backups
    fi

    # 生成报告
    if [ -n "$report_file" ]; then
        generate_report "$report_file"
    fi

    # 打印摘要
    if [ "$failed_only" = false ]; then
        print_summary
    else
        if [ ${#FAILED_FILES[@]} -gt 0 ]; then
            echo
            echo -e "${RED}失败的文件:${NC}"
            for file in "${FAILED_FILES[@]}"; do
                echo "  $(basename "$file")"
            done
        else
            echo -e "${GREEN}所有文件验证通过${NC}"
        fi
    fi

    # 返回退出码
    if [ $TOTAL_FAILED -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# 运行主程序
main "$@"
