#!/bin/bash

# ContentHub Skill - 多账号管理工具
# 用途：管理多个内容运营账号的微信公众号配置

# 设置 UTF-8 编码
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 列出所有配置的账号
list_accounts() {
    echo "📋 已配置的微信公众号账号："
    echo "=============================="

    # 读取当前激活的 AppID
    local current_app_id=""
    if [ -f "$ENV_FILE" ]; then
        current_app_id=$(grep "^WECHAT_APP_ID=" "$ENV_FILE" | cut -d'=' -f2)
    fi

    # 查找所有账号目录下的 .env.* 文件
    find "$PROJECT_ROOT" -maxdepth 2 -type f -name ".env.*" ! -name ".env.example" | while read -r env_file; do
        account_dir=$(dirname "$env_file")
        account_name=$(basename "$env_file" | sed 's/\.env\.//')

        # 读取 AppID
        app_id=$(grep "^WECHAT_APP_ID=" "$env_file" | cut -d'=' -f2)

        if [ -n "$app_id" ]; then
            # 判断是否为当前激活账号
            local is_current=""
            if [ "$app_id" = "$current_app_id" ]; then
                is_current=" ⭐ (当前激活)"
            fi

            echo "📱 $account_name$is_current"
            echo "   目录: $account_dir"
            echo "   AppID: $app_id"
            echo "   配置文件: $env_file"
            echo ""
        fi
    done
}

# 显示当前激活的账号
show_current_account() {
    echo "🔍 当前激活的账号："
    echo "=============================="

    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}❌ 未找到 .env 文件: $ENV_FILE${NC}"
        echo "   请先使用 'switch' 命令切换到某个账号"
        exit 1
    fi

    # 读取当前 AppID
    local current_app_id=$(grep "^WECHAT_APP_ID=" "$ENV_FILE" | cut -d'=' -f2)

    if [ -z "$current_app_id" ]; then
        echo -e "${YELLOW}⚠️  .env 文件中未配置 WECHAT_APP_ID${NC}"
        echo "   请使用 'switch' 命令切换到某个账号"
        exit 1
    fi

    # 查找匹配的账号
    local found=false
    local result_file=$(mktemp)

    find "$PROJECT_ROOT" -maxdepth 2 -type f -name ".env.*" ! -name ".env.example" | while read -r env_file; do
        account_dir=$(dirname "$env_file")
        account_name=$(basename "$env_file" | sed 's/\.env\.//')
        app_id=$(grep "^WECHAT_APP_ID=" "$env_file" | cut -d'=' -f2)

        if [ "$app_id" = "$current_app_id" ]; then
            echo "FOUND=true" >> "$result_file"
            echo "ACCOUNT_NAME=$account_name" >> "$result_file"
            echo "APP_ID=$app_id" >> "$result_file"
            echo "ACCOUNT_DIR=$account_dir" >> "$result_file"
            echo "ENV_FILE=$env_file" >> "$result_file"
            break
        fi
    done

    # 读取结果
    source "$result_file"
    rm -f "$result_file"

    if [ "$FOUND" = true ]; then
        echo -e "${GREEN}✅ 当前激活账号: $ACCOUNT_NAME${NC}"
        echo ""
        echo "📱 账号信息："
        echo "   AppID: $APP_ID"
        echo "   目录: $ACCOUNT_DIR"
        echo "   配置文件: $ENV_FILE"
        echo ""

        # 读取切换时间（如果存在）
        local switch_time=$(grep "# 切换时间:" "$ENV_FILE" | cut -d':' -f2- | sed 's/^[ ]*//')
        if [ -n "$switch_time" ]; then
            echo "⏰ 切换时间: $switch_time"
        fi
    else
        echo -e "${RED}❌ 未找到 AppID 对应的账号配置${NC}"
        echo "   当前 AppID: $current_app_id"
        echo ""
        echo "请检查："
        echo "1. 账号目录下是否存在 .env.<账号名> 文件"
        echo "2. 或者使用 'list' 命令查看所有已配置账号"
    fi
}

# 切换默认账号
switch_account() {
    local account_name="$1"

    if [ -z "$account_name" ]; then
        echo -e "${RED}❌ 请指定账号名称${NC}"
        echo "用法: manage-accounts.sh switch <账号名称>"
        exit 1
    fi

    # 查找账号配置文件
    local env_file="$PROJECT_ROOT/$account_name/.env.$account_name"

    if [ ! -f "$env_file" ]; then
        echo -e "${RED}❌ 未找到账号配置: $env_file${NC}"
        exit 1
    fi

    # 读取账号配置
    source "$env_file"

    if [ -z "$WECHAT_APP_ID" ] || [ -z "$WECHAT_APP_SECRET" ]; then
        echo -e "${RED}❌ 配置文件中缺少必要字段${NC}"
        exit 1
    fi

    # 备份项目根目录的 .env 文件
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$ENV_FILE.backup"
        echo -e "${YELLOW}📦 已备份现有 .env 文件${NC}"
    fi

    # 更新项目根目录 .env 文件中的微信配置
    # 保留其他配置，删除旧的微信配置（包括相关注释行）
    if [ -f "$ENV_FILE.backup" ]; then
        # 从备份文件中读取非微信配置的部分
        # 方法：删除所有包含 WECHAT_APP 的行及其相关的注释行
        # 先找到 WECHAT_APP_ID 所在行号，删除该行及其前面的注释行
        grep -v "WECHAT_APP" "$ENV_FILE.backup" | grep -v "# 默认微信公众号" | grep -v "# 账号配置文件:" | grep -v "# 切换时间:" | grep -v "# 注意：账号专属配置已迁移" | grep -v "# 以下为 MCP 配置文件引用的默认值" > "$ENV_FILE.tmp"
        mv "$ENV_FILE.tmp" "$ENV_FILE"
    fi

    # 添加新的微信配置
    {
        echo ""
        printf '# 默认微信公众号（%s）\n' "$account_name"
        printf '# 账号配置文件: %s/.env.%s\n' "$account_name" "$account_name"
        echo "# 切换时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "WECHAT_APP_ID=$WECHAT_APP_ID"
        echo "WECHAT_APP_SECRET=$WECHAT_APP_SECRET"
    } >> "$ENV_FILE"

    echo -e "${GREEN}✅ 已切换到账号: $account_name${NC}"
    echo "   AppID: $WECHAT_APP_ID"
    echo ""
    echo -e "${GREEN}🔄 项目环境变量已更新${NC}"
    echo "   项目 .env 文件已更新"
    echo ""

    # 更新 ~/.claude.json 中 wenyan-mcp 的环境变量
    update_claude_json_env "$account_name" "$WECHAT_APP_ID" "$WECHAT_APP_SECRET"

    echo -e "${YELLOW}⚠️  重要提示${NC}"
    echo "   wenyan-mcp 配置已更新到 ~/.claude.json"
    echo "   请重启 Claude Code 以使配置生效"
    echo ""
    echo "提示：备份文件已保存至 $ENV_FILE.backup"
}

# 更新 ~/.claude.json 中 wenyan-mcp 的环境变量
update_claude_json_env() {
    local account_name="$1"
    local app_id="$2"
    local app_secret="$3"
    local claude_json="$HOME/.claude.json"

    if [ ! -f "$claude_json" ]; then
        echo -e "${YELLOW}⚠️  未找到 ~/.claude.json 文件${NC}"
        return
    fi

    # 备份 .claude.json
    cp "$claude_json" "$claude_json.backup"
    echo -e "${YELLOW}📦 已备份 ~/.claude.json${NC}"

    # 使用 Python 更新 JSON 文件
    python3 - <<EOF
import json
import sys

claude_json_path = "$claude_json"
project_path = "$PROJECT_ROOT"
account_name = "$account_name"
app_id = "$app_id"
app_secret = "$app_secret"

try:
    with open(claude_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 确保 projects 和项目路径存在
    if 'projects' not in data:
        data['projects'] = {}

    if project_path not in data['projects']:
        data['projects'][project_path] = {}

    if 'mcpServers' not in data['projects'][project_path]:
        data['projects'][project_path]['mcpServers'] = {}

    # 更新 wenyan-mcp 的环境变量
    if 'wenyan-mcp' not in data['projects'][project_path]['mcpServers']:
        data['projects'][project_path]['mcpServers']['wenyan-mcp'] = {}

    data['projects'][project_path]['mcpServers']['wenyan-mcp']['type'] = 'stdio'
    data['projects'][project_path]['mcpServers']['wenyan-mcp']['command'] = 'npx'
    data['projects'][project_path]['mcpServers']['wenyan-mcp']['args'] = ['-y', '@wenyan-md/mcp']

    if 'env' not in data['projects'][project_path]['mcpServers']['wenyan-mcp']:
        data['projects'][project_path]['mcpServers']['wenyan-mcp']['env'] = {}

    data['projects'][project_path]['mcpServers']['wenyan-mcp']['env']['WECHAT_APP_ID'] = app_id
    data['projects'][project_path]['mcpServers']['wenyan-mcp']['env']['WECHAT_APP_SECRET'] = app_secret

    # 写回文件
    with open(claude_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已更新 ~/.claude.json 中的 wenyan-mcp 配置")
    print(f"   账号: {account_name}")
    print(f"   AppID: {app_id}")

except Exception as e:
    print(f"❌ 更新失败: {e}", file=sys.stderr)
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ~/.claude.json 更新成功${NC}"
    else
        echo -e "${RED}❌ ~/.claude.json 更新失败${NC}"
        echo "   请手动编辑 ~/.claude.json，在 projects['$PROJECT_ROOT'].mcpServers['wenyan-mcp'].env 中添加："
        echo "   WECHAT_APP_ID=$app_id"
        echo "   WECHAT_APP_SECRET=$app_secret"
        # 恢复备份
        mv "$claude_json.backup" "$claude_json"
    fi
}

# 添加新账号
add_account() {
    local account_name="$1"

    if [ -z "$account_name" ]; then
        echo -e "${RED}❌ 请指定账号名称${NC}"
        echo "用法: manage-accounts.sh add <账号名称>"
        exit 1
    fi

    # 检查账号目录是否存在
    local account_dir="$PROJECT_ROOT/$account_name"
    if [ ! -d "$account_dir" ]; then
        echo -e "${YELLOW}⚠️  账号目录不存在: $account_dir${NC}"
        read -p "是否创建? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$account_dir"
            echo -e "${GREEN}✅ 已创建账号目录${NC}"
        else
            exit 1
        fi
    fi

    echo "📝 添加新账号: $account_name"
    echo ""
    read -p "请输入微信公众号 AppID: " app_id
    read -sp "请输入微信公众号 AppSecret: " app_secret
    echo ""

    # 创建账号配置文件
    local env_file="$account_dir/.env.$account_name"
    cat > "$env_file" << EOF
# $account_name - 微信公众号配置
# 创建时间: $(date +%Y-%m-%d)

WECHAT_APP_ID=$app_id
WECHAT_APP_SECRET=$app_secret
EOF

    echo -e "${GREEN}✅ 账号配置已创建: $env_file${NC}"
    echo ""
    echo "📝 下一步操作："
    echo "1. 创建账号发布配置文件: $account_dir/publish-config.md"
    echo "2. 使用 'manage-accounts.sh switch $account_name' 切换到该账号"
    echo "3. 参考 .claude/skills/ContentHub/resources/config-templates/publish-config-template.md"
}

# 验证账号配置
validate_account() {
    local account_name="$1"

    if [ -z "$account_name" ]; then
        # 验证所有账号
        find "$PROJECT_ROOT" -maxdepth 2 -type f -name ".env.*" ! -name ".env.example" | while read -r env_file; do
            account_name=$(basename "$env_file" | sed 's/\.env\.//')
            validate_single_account "$account_name" "$env_file"
        done
    else
        local env_file="$PROJECT_ROOT/$account_name/.env.$account_name"
        validate_single_account "$account_name" "$env_file"
    fi
}

validate_single_account() {
    local account_name="$1"
    local env_file="$2"

    echo "验证账号: $account_name"
    echo "配置文件: $env_file"

    if [ ! -f "$env_file" ]; then
        echo -e "${RED}❌ 配置文件不存在${NC}"
        echo ""
        return
    fi

    # 检查必要字段
    if grep -q "^WECHAT_APP_ID=" "$env_file" && grep -q "^WECHAT_APP_SECRET=" "$env_file"; then
        echo -e "${GREEN}✅ 配置完整${NC}"
    else
        echo -e "${YELLOW}⚠️  配置不完整，缺少必要字段${NC}"
    fi
    echo ""
}

# 主命令
case "$1" in
    list)
        list_accounts
        ;;
    current)
        show_current_account
        ;;
    switch)
        switch_account "$2"
        ;;
    add)
        add_account "$2"
        ;;
    validate)
        validate_account "$2"
        ;;
    *)
        echo "ContentHub Skill - 多账号管理工具"
        echo ""
        echo "用法: $0 {list|current|switch|add|validate} [账号名称]"
        echo ""
        echo "命令说明:"
        echo "  list              - 列出所有已配置的账号"
        echo "  current           - 显示当前激活的账号"
        echo "  switch <账号名>   - 切换默认账号（更新项目 .env 文件）"
        echo "  add <账号名>      - 添加新账号"
        echo "  validate [账号名] - 验证账号配置"
        echo ""
        echo "账号切换机制:"
        echo "  - 更新项目根目录 .env 文件中的 WECHAT_APP_ID 和 WECHAT_APP_SECRET"
        echo "  - 更新 ~/.claude.json 中 wenyan-mcp 的环境变量配置"
        echo "  - wenyan-mcp 启动后自动使用新账号的微信凭证"
        echo ""
        echo "示例:"
        echo "  $0 list"
        echo "  $0 current"
        echo "  $0 switch 车界显眼包"
        echo "  $0 switch 吃货一本经"
        echo "  $0 add 新账号"
        echo "  $0 validate"
        exit 1
        ;;
esac
