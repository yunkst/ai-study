# 前端Docker构建文件 (开发模式 - 支持热重载)
FROM node:24.4.0

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖 (包括开发依赖)
RUN npm install

# 暴露端口
EXPOSE 3000

# 开发模式启动命令 (支持热重载)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 