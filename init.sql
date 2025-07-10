-- 软件架构师AI学习助手数据库初始化脚本
-- 这个文件会在PostgreSQL容器启动时自动执行

-- 创建数据库（如果不存在）
-- CREATE DATABASE IF NOT EXISTS tutor_db;

-- 设置数据库连接
\c tutor_db;

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 插入示例数据（可选）
-- 这些数据表会通过SQLAlchemy自动创建，这里只是示例

-- 示例题目数据
-- INSERT INTO questions (question_type, content, correct_answer, difficulty, knowledge_points, created_at) VALUES 
-- ('choice', '下列哪种设计模式属于创建型模式？', 'A', 1, '["设计模式", "创建型模式"]', NOW()),
-- ('choice', '微服务架构的主要优势是什么？', 'B', 2, '["微服务", "系统架构"]', NOW());

-- 设置权限
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO user;

-- 完成初始化
SELECT 'Database initialization completed!' AS status; 