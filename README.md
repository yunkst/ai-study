# 软件架构师AI学习助手

基于AI技术的个性化学习系统，采用前后端分离的微服务架构，支持智能练习、AI播客、学习分析等功能。

## 🏗️ 系统架构

### 微服务设计
- **前端服务** (3000): Vue3 + Nginx，用户界面和静态资源
- **后端服务** (8080): FastAPI，API接口和业务逻辑
- **数据库服务** (5432): PostgreSQL，数据持久化存储
- **缓存服务** (6379): Redis，缓存和会话管理

### 技术栈
- **前端**: Vue3 + TypeScript + Element Plus + Vite
- **后端**: FastAPI + SQLAlchemy + OpenAI + Edge TTS
- **数据库**: PostgreSQL + Redis
- **部署**: Docker + Nginx + Docker Compose

## 🚀 快速开始

### 一键部署
```bash
# 克隆项目
git clone [项目地址]
cd 学习辅助

# 配置环境变量（可选）
cp CONFIG.md .env
# 编辑 .env 文件设置 API KEY 等

# 启动所有服务
docker-compose up -d

# 测试服务状态
./test-services.bat   # Windows
./test-services.sh    # Linux/Mac
```

### 开发模式
```bash
# 后端开发
cd app/backend
pip install -r requirements.txt
python main.py

# 前端开发 (新终端)
cd app/frontend
npm install
npm run dev
```

### 测试运行
```bash
# 后端测试
cd app/backend
python test_runner.py           # 全部测试
python test_runner.py unit      # 单元测试
python test_runner.py coverage  # 代码覆盖率

# 前端测试
cd app/frontend
npm run test                    # 全部测试
npm run test:watch              # 监视模式
npm run test:ui                 # 测试UI界面
npm run test:coverage           # 代码覆盖率
```

### 独立部署
```bash
# 只启动后端相关服务
docker-compose up backend postgres redis

# 只启动前端服务
docker-compose up frontend

# 或者分别构建镜像
docker build -t ai-tutor-backend .
docker build -t ai-tutor-frontend app/frontend
```

## 🌐 访问地址

- **前端应用**: http://localhost:3000 (主要访问地址)
- **后端API**: http://localhost:8080/docs (API文档)
- **健康检查**: http://localhost:3000/health

## ✨ 功能特性

### 已实现框架
- ✅ 前后端完全分离架构
- ✅ Docker容器化部署
- ✅ 响应式用户界面
- ✅ API认证和权限控制
- ✅ 数据库模型和迁移
- ✅ AI服务集成框架
- ✅ TTS语音合成服务
- ✅ 后台任务调度系统
- ✅ 完整的测试框架
- ✅ 代码覆盖率报告

### 待开发功能
- 🔄 智能题库管理
- 🔄 个性化练习推荐
- 🔄 AI播客生成
- 🔄 学习数据分析
- 🔄 薄弱环节识别

## 📖 配置说明

详细配置请参考 [CONFIG.md](CONFIG.md) 文件。

## 🧪 测试指南

完整的测试框架配置请参考 [TESTING.md](TESTING.md) 文件。

### 主要环境变量
```bash
# AI服务（可选）
OPENAI_API_KEY=your-openai-key

# 访问控制（可选）
ACCESS_KEY=your-access-key

# 数据库（自动配置）
DATABASE_URL=postgresql://user:password@postgres:5432/tutor_db
```

## 🔧 开发指南

### 项目结构
```
学习辅助/
├── app/
│   ├── frontend/          # Vue3前端项目
│   │   ├── src/          # 源代码
│   │   ├── Dockerfile    # 前端容器
│   │   └── nginx.conf    # Nginx配置
│   └── backend/          # FastAPI后端项目
│       ├── api/          # API路由
│       ├── models/       # 数据模型
│       ├── services/     # 业务服务
│       └── core/         # 核心模块
├── docker-compose.yml    # 服务编排
├── Dockerfile           # 后端容器
└── init.sql            # 数据库初始化
```

### API开发
后端API使用FastAPI，支持自动API文档生成。访问 http://localhost:8080/docs 查看交互式API文档。

### 前端开发
前端使用Vue3 + TypeScript，支持热重载。开发时API请求会自动代理到后端服务。

## 🐳 Docker部署

项目支持完整的Docker化部署，包含：
- 前端Nginx静态文件服务
- 后端FastAPI应用服务  
- PostgreSQL数据库
- Redis缓存服务

所有服务通过内部网络通信，只暴露必要端口。

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

[添加许可证信息]