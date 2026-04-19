# ============ Stage 1: Build ============
FROM node:20-alpine AS builder

WORKDIR /app

# npm 换国内源
RUN npm config set registry https://registry.npmmirror.com

# 安装依赖（利用缓存）
COPY web/package*.json ./
RUN npm install

# 复制源代码并构建
COPY web/ .
RUN npm run build

# ============ Stage 2: Production ============
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
