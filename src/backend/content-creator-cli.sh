#!/bin/bash
# Content-Creator CLI 包装脚本
# 用于 ContentHub 调用 content-creator CLI

cd /Users/Oychao/Documents/Projects/content-creator

# 设置兼容的环境变量（转换为大写->小写）
case "${LOG_LEVEL:-ERROR}" in
  ERROR|error) export LOG_LEVEL_CREATOR=error ;;
  WARN|warn) export LOG_LEVEL_CREATOR=warn ;;
  INFO|info) export LOG_LEVEL_CREATOR=info ;;
  DEBUG|debug) export LOG_LEVEL_CREATOR=debug ;;
  *) export LOG_LEVEL_CREATOR=info ;;
esac

export NODE_ENV=${NODE_ENV:-development}

# 使用 content-creator 自己的日志级别
export LOG_LEVEL=$LOG_LEVEL_CREATOR

# 执行 pnpm run cli，并将所有参数传递
exec pnpm run cli "$@"
