# 数据库迁移指南

## 🗃️ Alembic 迁移系统

本项目已配置使用 **Alembic** 作为数据库迁移工具，支持数据库结构的版本控制和安全变更。

## 🐳 Docker 环境支持

项目针对 Docker 容器环境进行了优化：
- **启动时自动迁移**：容器启动时自动检查并应用数据库迁移
- **无感知更新**：模型变更后重启容器即可自动更新数据库
- **开发友好**：提供便捷的迁移管理脚本

## 📦 依赖管理（现代化）

本项目**已完全移除 requirements.txt**，统一采用 [PEP 621](https://peps.python.org/pep-0621/) 标准的 `pyproject.toml` 进行依赖管理。

- 生产环境依赖：`pip install .`
- 开发环境依赖：`pip install .[dev]`

> **Dockerfile 已自动使用 pyproject.toml 安装依赖，无需再维护 requirements.txt

## 📁 文件结构

```
app/backend/
├── alembic/
│   ├── versions/           # 迁移文件目录
│   ├── env.py             # 环境配置
│   └── script.py.mako     # 迁移模板
├── scripts/
│   └── migrate.py         # Docker环境迁移脚本
├── alembic.ini            # Alembic 配置文件
├── manage_db.py           # 本地开发管理脚本
├── dev_migrate.sh         # Docker开发便捷脚本
├── start.sh               # 容器启动脚本
├── pyproject.toml         # 现代依赖管理
└── core/database.py       # 数据库配置
```

## 🚀 快速开始

### Docker 环境（推荐）

#### 1. 自动迁移（无需手动操作）

```bash
# 启动服务（会自动处理数据库迁移）
docker compose up --build
```

容器启动时会自动：
- 等待数据库服务就绪
- 检查迁移历史并生成初始迁移（如果需要）
- 应用所有迁移到最新版本
- 启动应用服务

#### 2. 开发时管理迁移

```bash
# 创建新迁移
./app/backend/dev_migrate.sh create "描述你的更改"

# 查看当前版本
./app/backend/dev_migrate.sh current

# 查看迁移历史
./app/backend/dev_migrate.sh history

# 手动升级（通常不需要）
./app/backend/dev_migrate.sh upgrade
```

#### 3. 本地开发环境依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install .[dev]
```

### 本地开发环境

#### 1. 首次初始化（仅一次）

```bash
cd app/backend
pip install .[dev]
python manage_db.py init
```

这将：
- 根据当前模型生成初始迁移文件
- 应用迁移创建所有数据库表

#### 2. 后端自动迁移

后端启动时会自动运行 `alembic upgrade head`，确保数据库结构是最新的。

## 🔄 日常开发流程

### Docker 环境工作流（推荐）

#### 修改模型后的自动化流程

1. **修改模型文件**（如 `models/user.py`）
2. **生成迁移文件**：
   ```bash
   ./app/backend/dev_migrate.sh create "描述你的更改"
   ```
3. **检查生成的迁移文件**（在 `alembic/versions/` 目录中）
4. **重启容器应用迁移**（推荐）：
   ```bash
   docker compose restart backend
   ```
   或者手动升级：
   ```bash
   ./app/backend/dev_migrate.sh upgrade
   ```

#### Docker 示例工作流

```bash
# 1. 修改了用户模型，添加了新字段
./app/backend/dev_migrate.sh create "添加用户头像字段"

# 2. 查看迁移历史
./app/backend/dev_migrate.sh history

# 3. 重启容器自动应用迁移
docker compose restart backend

# 4. 查看当前版本
./app/backend/dev_migrate.sh current
```

### 本地开发环境工作流

#### 修改模型后创建迁移

1. **修改模型文件**（如 `models/user.py`）
2. **生成迁移文件**：
   ```bash
   python manage_db.py migrate "描述你的更改"
   ```
3. **检查生成的迁移文件**（在 `alembic/versions/` 目录中）
4. **应用迁移**：
   ```bash
   python manage_db.py upgrade
   ```
   或者重启后端服务（会自动应用）

#### 本地示例工作流

```bash
# 1. 修改了用户模型，添加了新字段
python manage_db.py migrate "添加用户头像字段"

# 2. 查看迁移历史
python manage_db.py history

# 3. 应用迁移
python manage_db.py upgrade

# 4. 查看当前版本
python manage_db.py current
```

## 📋 管理命令

### 常用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 初始化数据库（首次使用） | `python manage_db.py init` |
| `migrate` | 创建新迁移 | `python manage_db.py migrate "添加新表"` |
| `upgrade` | 升级到最新版本 | `python manage_db.py upgrade` |
| `downgrade` | 回滚到指定版本 | `python manage_db.py downgrade -1` |
| `history` | 显示迁移历史 | `python manage_db.py history` |
| `current` | 显示当前版本 | `python manage_db.py current` |

### 版本控制

```bash
# 升级到特定版本
python manage_db.py upgrade abc123

# 回滚一个版本
python manage_db.py downgrade -1

# 回滚到特定版本
python manage_db.py downgrade def456

# 回滚到初始状态
python manage_db.py downgrade base
```

## ⚠️ 注意事项

### 安全原则

1. **生产环境迁移前先备份数据库**
2. **在测试环境验证迁移后再应用到生产**
3. **仔细检查自动生成的迁移文件**
4. **避免删除迁移文件，使用 downgrade 回滚**

### 迁移文件检查

生成迁移后，检查 `alembic/versions/` 中的新文件：

```python
def upgrade() -> None:
    """升级数据库结构"""
    # 检查这些操作是否正确
    op.add_column('users', sa.Column('avatar', sa.String(255), nullable=True))

def downgrade() -> None:
    """回滚数据库结构"""
    # 确保回滚操作正确
    op.drop_column('users', 'avatar')
```

### 常见场景

#### 添加新表
```bash
python manage_db.py migrate "添加AI配置表"
```

#### 修改字段
```bash
python manage_db.py migrate "修改用户邮箱字段长度"
```

#### 添加索引
```bash
python manage_db.py migrate "为用户表添加邮箱索引"
```

#### 数据迁移
```bash
python manage_db.py migrate "迁移旧用户数据"
```

## 🔧 配置说明

### alembic.ini 配置

- **sqlalchemy.url**: 自动从 `core.config.settings.DATABASE_URL` 读取
- **script_location**: 迁移脚本位置（`alembic/`）

### env.py 配置

- **target_metadata**: 自动导入所有模型的元数据
- **异步支持**: 完整支持异步数据库操作

## 🐛 故障排除

### 迁移冲突

如果多人开发时出现迁移冲突：

1. **拉取最新代码**
2. **合并迁移**：
   ```bash
   alembic merge -m "合并迁移分支" head1 head2
   ```
3. **应用合并后的迁移**

### 迁移失败

如果迁移失败：

1. **检查错误信息**
2. **回滚到安全版本**：
   ```bash
   python manage_db.py downgrade -1
   ```
3. **修复问题后重新迁移**

### 重置数据库（开发环境）

如果需要完全重置：

1. **删除数据库**
2. **删除迁移文件**：
   ```bash
   rm alembic/versions/*.py
   ```
3. **重新初始化**：
   ```bash
   python manage_db.py init
   ```

## 📚 进阶用法

### 手动创建迁移

```bash
# 创建空迁移文件
alembic revision -m "自定义迁移"

# 基于模型差异创建迁移
alembic revision --autogenerate -m "自动生成迁移"
```

### 分支管理

```bash
# 创建分支
alembic branch -m "功能分支"

# 查看分支
alembic branches

# 合并分支
alembic merge -m "合并功能" head1 head2
```

## 🎯 最佳实践

1. **每次模型更改都创建迁移**
2. **迁移描述要清晰明确**
3. **定期检查迁移历史**
4. **生产部署前在测试环境验证**
5. **保持迁移文件的可读性**
6. **避免手动修改数据库结构** 