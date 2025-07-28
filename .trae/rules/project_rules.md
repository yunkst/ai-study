1. 禁止直接使用alembic命令，alembic需要在docker启动的时候自动执行升级和迁移。
2. 每次修改完前端页面都需要用 docker exec ai_study_frontend npm run lint 检查格式问题
3. 禁止使用 npm run dev 启动前端项目，前端项目已经用 docker 启动了，而且支持热重载，非必要不需要 docker restart
4. 禁止直接启动后端服务，后端服务已经用 docker 启动了，而且支持热重载，非必要不需要 docker restart