# 数据库迁移管理

本项目使用 Alembic 进行数据库迁移管理，支持自动检测模型变更并生成迁移脚本。

## 功能特性

- **自动迁移检查**: 应用启动时自动检查数据库模型变更
- **智能迁移生成**: 检测到变更时自动生成迁移脚本
- **安全迁移执行**: 先执行现有迁移，再检测新变更
- **CLI 管理工具**: 提供完整的数据库管理命令

## 启动时自动迁移

应用启动时会自动执行以下流程：

1. 检查数据库连接
2. 初始化 Alembic（如果未初始化）
3. 执行所有待应用的迁移
4. 检查模型是否有新变更
5. 如有变更，自动生成新的迁移脚本
6. 执行新生成的迁移

## 手动管理命令

### 基础命令

```bash
# 初始化数据库和 Alembic
python manage.py init-db

# 生成迁移脚本
python manage.py generate-migration "描述信息"

# 执行迁移
python manage.py migrate

# 检查数据库状态
python manage.py check-db

# 自动迁移（检查并执行）
python manage.py auto-migrate
```

### 高级用法

```bash
# 查看当前迁移状态
alembic current

# 查看迁移历史
alembic history

# 回滚到指定版本
alembic downgrade <revision>

# 升级到指定版本
alembic upgrade <revision>

# 查看 SQL 而不执行
alembic upgrade head --sql
```

## Docker 环境

在 Docker 环境中，启动脚本 `start.sh` 会自动处理：

1. 等待数据库服务就绪
2. 执行自动迁移检查
3. 启动 FastAPI 应用

## 注意事项

1. **模型变更**: 修改 `app/db/models.py` 中的模型后，重启应用会自动生成迁移
2. **手动迁移**: 复杂的数据迁移可能需要手动编辑生成的迁移文件
3. **生产环境**: 建议在生产环境中先备份数据库再执行迁移
4. **版本控制**: 生成的迁移文件应该提交到版本控制系统
5. **依赖管理**: 项目使用 uv 和 pyproject.toml 进行依赖管理

## 故障排除

### 常见问题

1. **迁移冲突**: 多人开发时可能出现迁移版本冲突
   ```bash
   alembic merge heads
   ```

2. **迁移失败**: 检查数据库连接和权限
   ```bash
   python manage.py check-db
   ```

3. **重置迁移**: 开发环境中重置所有迁移
   ```bash
   # 删除 alembic/versions/ 下的所有文件
   # 重新初始化
   python manage.py init-db
   ```

## 文件结构

```
backend/
├── alembic/
│   ├── versions/          # 迁移脚本目录
│   ├── env.py            # Alembic 环境配置
│   └── script.py.mako    # 迁移脚本模板
├── alembic.ini           # Alembic 配置文件
├── pyproject.toml        # 项目配置和依赖管理
├── manage.py             # 数据库管理 CLI
├── start.sh              # Docker 启动脚本
└── app/
    ├── db/
    │   ├── models.py     # 数据库模型
    │   └── database.py   # 数据库连接
    └── services/
        └── migration_service.py  # 迁移服务
```