# ==================== Build Stage ====================
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装所有依赖（包括 devDependencies，构建需要 vite）
RUN npm ci && \
    npm cache clean --force

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# ==================== Production Stage ====================
FROM nginx:alpine

# 安装 curl 用于健康检查
RUN apk --no-cache add curl

# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 从构建阶段复制静态文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建 nginx 缓存目录
RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 启动 nginx（使用前台模式）
CMD ["nginx", "-g", "daemon off;"]
