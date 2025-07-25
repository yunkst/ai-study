# 功能

1. 手机APP离线刷题
2. 在有服务的地方，同步刷题数据
3. 在服务的地方，提供AI问答功能

# 架构

后端采用 fastapi+ postgres,通过 almebic 进行数据库升级和管理
后台前端采用 vue3+ element-plus
APP用flutter实现
AI服务通过dify提供，由后端进行转发流式接口

题目可以从后端下载到APP，进行离线刷题。

除了APP都是部署在 docker上，可以通过docker-compose 一键启动，docker 部署后支持热更新

后端服务启动的时候，需要检查数据库模型是否变更，如果变更就自动用alembic生成迁移脚本（如果已有迁移脚本，则先进行迁移后再进行检测）

后端服务用 uv 进行依赖管理，依赖配置通过 pyproject.toml
